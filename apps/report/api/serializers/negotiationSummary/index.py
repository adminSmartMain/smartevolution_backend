# Rest Framework
from rest_framework import serializers
# Serializers
from apps.report.api.serializers.pendingAccount.index import PendingAccountSerializer
from apps.administration.api.serializers.emitterDeposit.index import EmitterDepositSerializer
from apps.administration.api.serializers.accountingControl.index import AccountingControlSerializer
# Utils
from apps.report.api.models.index import NegotiationSummary
from django.utils import timezone
from decimal import Decimal
from apps.base.utils.index import gen_uuid
# Exceptions
from apps.base.exceptions import HttpException

# Models 
from apps.report.api.models.pendingAccounts.index import PendingAccount
from apps.administration.api.models.emitterDeposit.index import EmitterDeposit
from apps.operation.models import PreOperation
from apps.operation.utils.penny_allocation import as_decimal, build_summary_settlement, round_cop, settle_operations
import logging

# Configurar el logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Crear un handler de consola y definir el nivel
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Crear un formato para los mensajes de log
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Añadir el handler al logger
logger.addHandler(console_handler)

class NegotiationSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = NegotiationSummary
        fields = '__all__'

    def create(self, validated_data):
        self._apply_settlement(validated_data)
        validated_data['id'] = gen_uuid()
        validated_data['created_at'] = timezone.now()
        validated_data['user_created_at'] = self.context['request'].user
        # create the pending Accounts of the operation
        if 'pendingAccounts' in self.context['request'].data:
            for x in self.context['request'].data['pendingAccounts']:
                print(x)
                serializer = PendingAccountSerializer(data=x, context={'request': self.context['request']})
                if serializer.is_valid():
                    serializer.save()
        return NegotiationSummary.objects.create(**validated_data)

    def update(self, instance, validated_data):
        self._apply_settlement(validated_data, fallback_op_id=instance.opId)
        validated_data['user_updated_at'] = self.context['request'].user
        validated_data['updated_at']      = timezone.now()
        if 'pendingAccounts' in self.context['request'].data:
            pendingAccount = PendingAccount.objects.filter(opId=validated_data['opId']).delete()
            for x in self.context['request'].data['pendingAccounts']:
                # add op id to the pending account
                x['opId'] = validated_data['opId']
                serializer = PendingAccountSerializer(data=x, context={'request': self.context['request']})
                if serializer.is_valid():
                    serializer.save()
                else:
                    raise HttpException(400, serializer.errors)

        return super().update(instance, validated_data)

    def _apply_settlement(self, validated_data, fallback_op_id=None):
        """Settle detail rows and derive headers in one backend-owned path."""
        op_id = validated_data.get('opId', fallback_op_id)
        if not op_id:
            return
        operations = list(
            PreOperation.objects.select_for_update().filter(opId=op_id).order_by('id')
        )
        if not operations:
            raise serializers.ValidationError({'opId': 'La operación no tiene detalles para liquidar.'})

        settle_operations(operations)
        settlement = build_summary_settlement(operations, validated_data)
        pending_accounts = self.context['request'].data.get('pendingAccounts', [])
        total_discounts = sum(
            (as_decimal(item.get('amount')) for item in pending_accounts), Decimal('0')
        )
        total_deposits = sum(
            (as_decimal(deposit.settledAmount if deposit.settledAmount is not None else deposit.amount)
             for deposit in EmitterDeposit.objects.filter(operation__opId=op_id, state=1)),
            Decimal('0'),
        )
        settlement['totalDiscounts'] = round_cop(total_discounts)
        settlement['total'] = round_cop(
            settlement['valueToDiscount'] - settlement['investorDiscount'] - settlement['billValue'] - settlement['totalDiscounts']
        )
        manual_adjustment = round_cop(validated_data.get('manualAdjustment', 0))
        validated_data['manualAdjustment'] = manual_adjustment
        settlement['pendingToDeposit'] = round_cop(settlement['total'] - total_deposits - manual_adjustment)
        for field, value in settlement.items():
            # The legacy fields remain integer-valued for compatibility with
            # existing clients. The settled fields are the legal-document SSOT.
            validated_data[field] = int(value)
            settled_field = 'settled' + field[0].upper() + field[1:]
            validated_data[settled_field] = value


class NegotiationSummaryReadOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = NegotiationSummary
        fields = '__all__'

    def to_representation(self, instance):
        #accountingControl = []
        data = super().to_representation(instance)
       
        data['pendingAccounts']  = PendingAccountSerializer(PendingAccount.objects.filter(opId=instance.opId), many=True).data
        
     
        data['emitterDeposits']  = EmitterDepositSerializer(EmitterDeposit.objects.filter(operation__opId=instance.opId), many=True).data
        
        data['totalDeposits'] = sum(
            (deposit.settledAmount if deposit.settledAmount is not None else deposit.amount
             for deposit in EmitterDeposit.objects.filter(operation__opId=instance.opId, state=True)),
            Decimal('0'),
        )
        data['pendingToDeposit'] = (
            instance.settledPendingToDeposit
            if instance.settledPendingToDeposit is not None
            else data['total'] - data['totalDeposits']
        )
        # get the account control of the emitter deposits
        #for x in data['emitterDeposits']:
            # get the account control of the emitter deposit
        #    accountingControlData = AccountingControlSerializer(AccountingControlSerializer.Meta.model.objects.get(emitterDeposit__id=x['id'])).data
        #    accountingControl.append(accountingControlData)
        #data['accountingControl'] = accountingControl
        return data
