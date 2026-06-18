# Rest Framework
from rest_framework import serializers
from django.db import transaction
from django.utils import timezone

# Models
from apps.operation.models import Receipt, ReceiptSnapshot

# Serializers
from apps.operation.api.serializers.index import PreOperationReadOnlySerializer
from apps.misc.api.serializers.index import TypeReceiptSerializer, ReceiptStatusSerializer
from apps.client.api.serializers.index import AccountSerializer

# Utils
from apps.base.utils.index import gen_uuid
from apps.base.utils.logBalanceAccount import log_balance_change

# Exceptions
from apps.base.exceptions import HttpException

# Enums
from apps.operation.enums import ReceiptStatusEnum

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(console_handler)


FINANCIAL_UPDATE_FIELDS = {
    "date",
    "operation",
    "typeReceipt",
    "receiptStatus",
    "account",
    "realDays",
    "additionalDays",
    "calculatedDays",
    "additionalInterests",
    "additionalInterestsSM",
    "investorInterests",
    "tableInterests",
    "futureValueRecalculation",
    "tableRemaining",
    "remaining",
    "payedAmount",
    "presentValueInvestor",
}


def get_last_active_receipt(operation_id):
    return (
        Receipt.objects
        .filter(
            operation_id=operation_id,
            state=1,
            controlStatus=Receipt.CONTROL_ACTIVE,
        )
        .order_by("-date", "-created_at", "-dId", "-id")
        .first()
    )


def is_last_active_receipt(receipt):
    if not receipt or not getattr(receipt, "state", None):
        return False

    if getattr(receipt, "controlStatus", Receipt.CONTROL_ACTIVE) != Receipt.CONTROL_ACTIVE:
        return False

    last_receipt = get_last_active_receipt(receipt.operation_id)

    if not last_receipt:
        return False

    return str(last_receipt.id) == str(receipt.id)


def validate_receipt_date_order(operation_id, receipt_date):
    last_receipt = get_last_active_receipt(operation_id)

    if not last_receipt:
        return

    if receipt_date and last_receipt.date and receipt_date < last_receipt.date:
        raise HttpException(
            400,
            "La fecha del recaudo no puede ser menor a la fecha del último recaudo activo de la operación.",
        )


def build_snapshot_before(operation, account):
    bill = getattr(operation, "bill", None)

    return {
        "operationStatusBefore": getattr(operation, "status", None),
        "operationPendingBefore": getattr(operation, "opPendingAmount", None),
        "operationAmountBefore": getattr(operation, "amount", None),
        "operationPayedAmountBefore": getattr(operation, "payedAmount", None),
        "accountBalanceBefore": getattr(account, "balance", None) if account else None,
        "billCurrentBalanceBefore": getattr(bill, "currentBalance", None) if bill else None,
        "billReBuyAvailableBefore": getattr(bill, "reBuyAvailable", None) if bill else None,
    }


def build_snapshot_after(operation, account):
    bill = getattr(operation, "bill", None)

    return {
        "operationStatusAfter": getattr(operation, "status", None),
        "operationPendingAfter": getattr(operation, "opPendingAmount", None),
        "operationAmountAfter": getattr(operation, "amount", None),
        "operationPayedAmountAfter": getattr(operation, "payedAmount", None),
        "accountBalanceAfter": getattr(account, "balance", None) if account else None,
        "billCurrentBalanceAfter": getattr(bill, "currentBalance", None) if bill else None,
        "billReBuyAvailableAfter": getattr(bill, "reBuyAvailable", None) if bill else None,
    }


class ReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data):
        try:
            validated_data['id'] = validated_data.get('id') or gen_uuid()

            account = validated_data['account']
            operation = validated_data['operation']
            user = self.context['request'].user

            validate_receipt_date_order(operation.id, validated_data.get('date'))

            snapshot_before = build_snapshot_before(operation, account)

            # Recompra.
            if validated_data['receiptStatus'].id == ReceiptStatusEnum.RECOMPRA.value:
                operation.bill.currentBalance = operation.bill.total
                operation.bill.reBuyAvailable = True
                operation.bill.save()
                operation.status = 4
                operation.opPendingAmount = 0
                operation.save()

                movement_value = round(
                    validated_data['presentValueInvestor'] + validated_data['investorInterests'],
                    2,
                )
                log_balance_change(
                    account,
                    account.balance,
                    account.balance + movement_value,
                    movement_value,
                    'receipt',
                    validated_data['id'],
                    'Receipt - create recompra',
                )
                account.balance += movement_value
                account.save()
            else:
                # Recaudo cancelado.
                if validated_data['typeReceipt'].id in ReceiptStatusEnum.CANCELED_STATUSES.value:
                    operation.status = 4
                    operation.opPendingAmount = 0
                    operation.save()
                else:
                    # Recaudo parcial.
                    operation.opPendingAmount -= round(
                        (validated_data['payedAmount'] - validated_data['additionalInterests']),
                        2,
                    )
                    operation.save()

                movement_value = round(
                    (validated_data['presentValueInvestor'] + validated_data['investorInterests']),
                    2,
                )
                log_balance_change(
                    account,
                    account.balance,
                    account.balance + movement_value,
                    movement_value,
                    'receipt',
                    validated_data['id'],
                    'Receipt - create',
                )
                account.balance += movement_value
                account.save()

            try:
                last_receipt = Receipt.objects.all().order_by('-dId').first()
                if last_receipt and last_receipt.dId is not None:
                    validated_data['dId'] = last_receipt.dId + 1
                else:
                    validated_data['dId'] = 1
            except Exception:
                validated_data['dId'] = 1

            validated_data['created_at'] = timezone.now()
            validated_data['user_created_at_id'] = user.id
            validated_data.setdefault('controlStatus', Receipt.CONTROL_ACTIVE)

            receipt = Receipt.objects.create(**validated_data)

            snapshot_after = build_snapshot_after(operation, account)
            ReceiptSnapshot.objects.create(
                id=gen_uuid(),
                receipt=receipt,
                **snapshot_before,
                **snapshot_after,
                user_created_at_id=user.id,
            )

            return receipt
        except Exception as e:
            raise HttpException(400, e)

    def update(self, instance, validated_data):
        try:
            requested_financial_fields = FINANCIAL_UPDATE_FIELDS.intersection(set(validated_data.keys()))

            if requested_financial_fields:
                raise HttpException(
                    400,
                    "No se permite actualizar campos financieros directamente. Use el flujo de ajuste/anulación del recaudo.",
                )

            for field, value in validated_data.items():
                setattr(instance, field, value)

            instance.updated_at = timezone.now()
            instance.user_updated_at = self.context['request'].user
            instance.save()
            return instance
        except Exception as e:
            raise HttpException(400, e)


class ReceiptReadOnlySerializer(serializers.ModelSerializer):
    operation = PreOperationReadOnlySerializer(read_only=True)
    typeReceipt = TypeReceiptSerializer(read_only=True)
    account = AccountSerializer(read_only=True)
    receiptStatus = ReceiptStatusSerializer(read_only=True)
    canEdit = serializers.SerializerMethodField()
    canVoid = serializers.SerializerMethodField()
    blockReason = serializers.SerializerMethodField()

    class Meta:
        model = Receipt
        fields = '__all__'

    def get_canEdit(self, obj):
        return is_last_active_receipt(obj)

    def get_canVoid(self, obj):
        return is_last_active_receipt(obj)

    def get_blockReason(self, obj):
        if self.get_canEdit(obj):
            return None

        if not obj.state:
            return "Este recaudo ya no está activo."

        if getattr(obj, "controlStatus", Receipt.CONTROL_ACTIVE) != Receipt.CONTROL_ACTIVE:
            return "Este recaudo ya fue anulado o ajustado."

        return "Solo se puede modificar el último recaudo activo de la operación."
