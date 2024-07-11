# Rest Framework
from rest_framework import serializers
# Serializers
from apps.bill.api.serializers.bill.index import BillSerializer
from apps.client.api.serializers.client.index import ClientSerializer
from apps.client.api.serializers.broker.index import BrokerSerializer
from apps.misc.api.serializers.typeOperation.index import TypeOperationSerializer
from apps.client.api.serializers.account.index import AccountSerializer
# Models
from apps.operation.models import PreOperation, BuyOrder,Receipt
from apps.report.models import SellOrder
from apps.client.models import RiskProfile
# Utils
from django.utils import timezone
from apps.base.utils.index import gen_uuid
from apps.report.utils.electronicSignatureAPI import getSignatureStatus
import requests
import datetime
# Exceptions
from apps.base.exceptions import HttpException

class PreOperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreOperation
        fields = '__all__'

    def create(self, validated_data):
        validated_data['id'] = gen_uuid()
        validated_data['created_at'] = timezone.now()
        validated_data['user_created_at'] = None
        # validate if the bill amount is greater than the total amount of the operation
        if validated_data['bill'] != None:
            #if validated_data['bill'].currentBalance < validated_data['payedAmount']:
            #    raise HttpException(400, 'el monto de la factura es menor al monto total de la operacion')
            # validate if the client account has enough balance
            if validated_data['clientAccount'].balance < (validated_data['payedAmount'] + validated_data['GM']):
                validated_data['insufficientAccountBalance'] = True
            else:
                validated_data['insufficientAccountBalance'] = False

            validated_data['bill'].currentBalance -= validated_data['payedAmount']
            validated_data['opPendingAmount'] = validated_data['amount']
            validated_data['bill'].save()
        return  super().create(validated_data)

    def update(self, instance, validated_data):

        validated_data['user_updated_at'] = self.context['request'].user
        validated_data['updated_at']      = timezone.now()

        if 'previousDeleted' in self.context['request'].data:
            validated_data['status'] = 0
            instance.bill.currentBalance -= instance.payedAmount
            instance.bill.save()

        if  validated_data['status'] != 0 and validated_data['status'] != 1:
            if validated_data['status'] == 2 or validated_data['status'] == 5:
                instance.bill.currentBalance   += instance.payedAmount
                instance.bill.save()

        if validated_data['status'] == 1 and instance.status == 0:
            instance.clientAccount.balance -= (instance.presentValueInvestor + instance.GM)
            instance.clientAccount.save()

        # reverse the payed amount to the operation bill
        if 'payedAmount' in validated_data:
            validated_data['bill'].currentBalance += instance.payedAmount
            validated_data['bill'].currentBalance -= validated_data['payedAmount']
            validated_data['bill'].save()
            validated_data['opPendingAmount'] = validated_data['payedAmount']
        # if the operation has a buyorder set it to 0
        buyOrder = BuyOrder.objects.filter(operation_id=instance.id, state = 1)
        for x in buyOrder:
            x.state = 0
            x.save()
        return super().update(instance, validated_data)


class PreOperationReadOnlySerializer(serializers.ModelSerializer):
    bill           = BillSerializer(read_only=True)
    emitter        = ClientSerializer(read_only=True)
    investor       = ClientSerializer(read_only=True)
    payer          = ClientSerializer(read_only=True)
    emitterBroker  = BrokerSerializer(read_only=True)
    investorBroker = BrokerSerializer(read_only=True)
    opType         = TypeOperationSerializer(read_only=True)
    clientAccount  = AccountSerializer(read_only=True)
    previousOperationBill = serializers.SerializerMethodField(method_name='get_previous_operation_bill')
    previousOperationData = serializers.SerializerMethodField(method_name='get_previous_operation_data')
    isPartiallyPayed = serializers.SerializerMethodField(method_name='get_is_partially_payed')
    class Meta:
        model = PreOperation
        fields = '__all__'

    def get_previous_operation_bill(self, obj):
        previousOperation = PreOperation.objects.filter(bill=obj.bill).order_by('-created_at').exclude(id=obj.id).first()        
        if previousOperation != None and obj.isRebuy == True:
            return {
                'date': previousOperation.opDate,
                'discountTax': previousOperation.discountTax,
                'opId': previousOperation.opId,
            }
        else:
            return None
        
    def get_previous_operation_data(self, obj):
        # get the operation bill receipts
        receipts = Receipt.objects.filter(operation__bill=obj.bill,receiptStatus='ea8518e8-168a-46d7-b56a-1286bf0037cd').order_by('-created_at').first()
        if receipts != None and obj.bill.reBuyAvailable == True:
            return {
                'date': receipts.operation.opDate,
                'discountTax': receipts.operation.discountTax,
                'opId': receipts.operation.opId,
            }
        else:
            return None
    
    
    def get_is_partially_payed(self, obj):
        if obj.payedAmount > obj.opPendingAmount and obj.opPendingAmount > 0:
            return True
        else:
            return False

class PreOperationSignatureSerializer(serializers.ModelSerializer):
    bill           = BillSerializer(read_only=True)
    emitter        = ClientSerializer(read_only=True)
    investor       = ClientSerializer(read_only=True)
    payer          = ClientSerializer(read_only=True)
    isSellOrderSent = serializers.SerializerMethodField(method_name='get_is_buy_order_sent')
    billCount  = serializers.SerializerMethodField(method_name='get_number_of_bills')
    promDays   = serializers.SerializerMethodField(method_name='get_prom_days')
    isSignatureSent  = serializers.SerializerMethodField(method_name='get_is_signature_sent')
    signStatusDate   = serializers.SerializerMethodField(method_name='get_sign_status_date')
    buyOrderSentDate = serializers.SerializerMethodField(method_name='get_buy_order_sent_date')
    isPartiallyPayed = serializers.SerializerMethodField(method_name='get_is_partially_payed')

    class Meta:
        model = PreOperation
        fields = '__all__'

    def get_is_signature_sent(self, obj):
        try:
            isSent = False
            # get the complete operation
            operation = PreOperation.objects.filter(opId=obj.opId, investor=obj.investor)
            # check if any operation with the same opId has a signature
            for x in operation:
                try:
                    # validate if the operation has a signature
                    buyOrder = BuyOrder.objects.get(operation_id=x.id)
                    isSent = True
                    break
                except:
                    pass
            return isSent

        except:
            return False
        
    def get_is_buy_order_sent(self, obj):
        try:
            isSellOrderSent = False
            # get the buyOrder
            sellOrder = SellOrder.objects.get(opId=obj.opId, client_id=obj.investor.id,state=1)
            isSellOrderSent = True
            return isSellOrderSent
        except:
            return False
        g
    def get_number_of_bills(self, obj):
        try:
            # get the complete operation
            operation = PreOperation.objects.filter(opId=obj.opId, investor=obj.investor)
            return operation.count()
        except:
            return 0
    
    def get_prom_days(self, obj):
        try:
            # get the complete operation
            operation = PreOperation.objects.filter(opId=obj.opId)
            # get the days
            days = 0
            for x in operation:
                days += x.operationDays
            return days / operation.count()
        except:
            return 0
        
    def get_sign_status_date(self, obj):
        try:
            # get the buy order
            buyOrder = BuyOrder.objects.get(operation_id=obj.id)
            signatureStatus = getSignatureStatus(buyOrder.code)
            valid = False
            # check if all the signatures are finished
            for x in signatureStatus['message']['data']['signProfile']:
                if x['status'] == 'FINISH':
                    valid = True
                else:
                    valid = False
                    break
            if valid == True:
                return signatureStatus['message']['data']['updatedAt']
            else:
                return None

        except Exception as e:
            return None
    
    def get_buy_order_sent_date(self, obj):
        try:
            # get the buy order
            buyOrder = BuyOrder.objects.get(operation_id=obj.id, state=1)
            return buyOrder.created_at
        except:
            return None
        
    def get_is_partially_payed(self, obj):
        if obj.payedAmount > obj.opPendingAmount and obj.opPendingAmount > 0:
            return True
        else:
            return False
        


class PreOperationByParamsSerializer(serializers.ModelSerializer):
    #bill           = BillSerializer(read_only=True)
    #emitter        = ClientSerializer(read_only=True)
    #investor       = ClientSerializer(read_only=True)
    #payer          = ClientSerializer(read_only=True)
    #opType         = TypeOperationSerializer(read_only=True)
    billData       = serializers.SerializerMethodField(method_name='get_bill_data')
    emitterName    = serializers.SerializerMethodField(method_name='get_emitter_name')
    investorName   = serializers.SerializerMethodField(method_name='get_investor_name')
    payerName      = serializers.SerializerMethodField(method_name='get_payer_name')
    isPartiallyPayed = serializers.SerializerMethodField(method_name='get_is_partially_payed')

    class Meta:
        model = PreOperation
        fields = '__all__'

    def get_bill_data(self, obj):
        return obj.bill.billId
    
    def get_emitter_name(self, obj):
        return obj.emitter.social_reason if obj.emitter.social_reason else obj.emitter.first_name + ' ' + obj.emitter.last_name

    def get_payer_name(self, obj):
        return obj.payer.social_reason if obj.payer.social_reason else obj.payer.first_name + ' ' + obj.payer.last_name
    
    def get_investor_name(self, obj):
        return obj.investor.social_reason if obj.investor.social_reason else obj.investor.first_name + ' ' + obj.investor.last_name

    def get_is_partially_payed(self, obj):
        
        if obj.payedAmount > obj.opPendingAmount and obj.opPendingAmount > 0:
            return True
        else:
            return False




