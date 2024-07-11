# Rest Framework
from rest_framework import serializers
from django.db import transaction
# Utils
from apps.operation.models import Receipt
# Serializers
from apps.operation.api.serializers.index import PreOperationSerializer
from apps.misc.api.serializers.index import TypeReceiptSerializer, ReceiptStatusSerializer
from apps.client.api.serializers.index import AccountSerializer
from django.utils import timezone
from apps.base.utils.index import gen_uuid
# Exceptions
from apps.base.exceptions import HttpException
# Enums
from apps.operation.enums import ReceiptStatusEnum


class ReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data):
        try:
            account   = validated_data['account']
            operation = validated_data['operation']
            
            # check if the receiptStatus is "recompra"
            if validated_data['receiptStatus'].id == ReceiptStatusEnum.RECOMPRA.value:
                operation.bill.currentBalance = operation.bill.total
                operation.bill.reBuyAvailable = True
                operation.bill.save()
                operation.status = 4
                operation.opPendingAmount = 0
                operation.save()
                account.balance += round(validated_data['investorInterests'],2)
                account.save()
            else:
                # check if the receiptStatus is canceled
                if validated_data['typeReceipt'].id in ReceiptStatusEnum.CANCELED_STATUSES.value:
                    operation.status = 4
                    operation.opPendingAmount = 0
                    operation.save()
                else:
                    # subtract of the amount paid to the operation
                    operation.opPendingAmount -= round((validated_data['payedAmount'] - validated_data['additionalInterests']), 2)
                    operation.save()
                # add the presentValueInvestor and investor interests to the account
                account.balance += round((validated_data['presentValueInvestor'] + validated_data['investorInterests']), 2)
                account.save()

            # create the receipt
            try:
                last_deposit = Receipt.objects.all().order_by('-dId').first()
                if last_deposit.dId != None:
                    validated_data['dId'] = last_deposit.dId + 1
            except Receipt.DoesNotExist:
                validated_data['dId'] = 1
            except Exception as e:
                validated_data['dId'] = 1

            validated_data['id']              = gen_uuid()
            validated_data['created_at']      = timezone.now()
            validated_data['user_created_at'] = None
            return Receipt.objects.create(**validated_data)
                
        except Exception as e:
            raise HttpException(400, e)
    
    def update(self, instance, validated_data):
        try:
            #create the receipt
            instance.updated_at      = timezone.now()
            instance.user_updated_at = self.context['request'].user
            instance.save()
            return instance
        except Exception as e:
            raise HttpException(400, e)

class ReceiptReadOnlySerializer(serializers.ModelSerializer):
    operation     = PreOperationSerializer(read_only=True)
    typeReceipt   = TypeReceiptSerializer(read_only=True)
    account       = AccountSerializer(read_only=True)
    receiptStatus = ReceiptStatusSerializer(read_only=True)
    class Meta:
        model = Receipt
        fields = '__all__'