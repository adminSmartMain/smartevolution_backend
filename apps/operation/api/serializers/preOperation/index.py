# Rest Framework
from rest_framework import serializers
# Serializers
from apps.bill.api.serializers.bill.index import BillSerializer
from apps.client.api.serializers.client.index import ClientSerializer
from apps.client.api.serializers.broker.index import BrokerSerializer
from apps.misc.api.serializers.typeOperation.index import TypeOperationSerializer
from apps.client.api.serializers.account.index import AccountSerializer
from apps.base.utils.index import gen_uuid, PDFBase64File, uploadFileBase64
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
#utils
from apps.base.utils.logBalanceAccount import log_balance_change
import logging
import uuid

from apps.bill.api.models.bill.index import Bill

from django.conf import settings


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

def is_uuid(val):
        try:
            uuid.UUID(str(val))
            return True
        except ValueError:
            return False
class PreOperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreOperation
        fields = '__all__'

      

    def validate(self, data):
        # Si viene billCode, lo convertimos a bill (ID)
        if 'billCode' in data and data['billCode']:
            logger.debug(f"Validando billCode: {data['billCode']}")
            try:
                bill = Bill.objects.get(billId=data['billCode'])
                logger.debug(f"Factura encontrada: {bill.id}")
                data['bill'] = bill.id
            except Bill.DoesNotExist:
                raise serializers.ValidationError({
                    'bill': f"La factura {data['billCode']} no existe"
                })
        # Si viene bill como string (billId), lo convertimos a ID
        elif 'bill' in data and isinstance(data['bill'], str) and not is_uuid(data['bill']):
            logger.debug(f"Validando billId: {data['bill']}")
            try:
                bill = Bill.objects.get(billId=data['bill'])
                logger.debug(f"Factura encontrada: {bill.id}")
                data['bill'] = bill.id
                logger.debug(f"Factura convertida a ID: {data['bill']}")
            except Bill.DoesNotExist:
                raise serializers.ValidationError({
                    'bill': f"La factura {data['bill']} no existe"
                })
        
        return data

    def create(self, validated_data):
        logger.info("Iniciando creación de PreOperation")
        logger.debug(f"Datos validados: {validated_data}")
        
        try:
            validated_data['id'] = gen_uuid()
            validated_data['created_at'] = timezone.now()
            validated_data['user_created_at'] = self.context['request'].user

            if validated_data.get('bill'):
                bill = validated_data['bill']
                logger.debug(f"Procesando factura asociada: {bill.billId}")
                
                client_account = validated_data.get('clientAccount')
                if client_account:
                    total_operation = validated_data['payedAmount'] + validated_data.get('GM', 0)
                    validated_data['insufficientAccountBalance'] = client_account.balance < total_operation
                    logger.debug(f"Validación de saldo: {validated_data['insufficientAccountBalance']}")

                if bill.currentBalance != 0:
                    logger.debug(f"Ajustando balance de factura: {bill.currentBalance} -> {bill.currentBalance - validated_data['amount']}")
                    bill.currentBalance -= validated_data['amount']
                    bill.save()


                
                validated_data['opPendingAmount'] = validated_data['payedAmount']
            
            instance = super().create(validated_data)
            logger.info(f"PreOperation creada exitosamente: {instance.id}")
            return instance

        except Exception as e:
            logger.error(f"Error al crear PreOperation: {str(e)}", exc_info=True)
            raise

    def update(self, instance, validated_data):

        validated_data['user_updated_at'] = self.context['request'].user
        validated_data['updated_at']      = timezone.now()

        if 'previousDeleted' in self.context['request'].data:
            validated_data['status'] = 0
            instance.bill.currentBalance -= instance.amount
            instance.bill.save()

        if  validated_data['status'] != 0 and validated_data['status'] != 1:
            if validated_data['status'] == 2 or validated_data['status'] == 5:
                instance.bill.currentBalance   += instance.amount
                instance.bill.save()

        if validated_data['status'] == 1 and instance.status == 0:
            log_balance_change(instance.clientAccount, instance.clientAccount.balance, (instance.clientAccount.balance - (instance.presentValueInvestor + instance.GM)), -(instance.presentValueInvestor + instance.GM), 'pre_operation', instance.id, 'PreOperation - update')

            instance.clientAccount.balance -= (instance.presentValueInvestor + instance.GM)
            instance.clientAccount.save()

        # reverse the payed amount to the operation bill
        if 'amount' in validated_data:
            validated_data['bill'].currentBalance += instance.amount
            if validated_data['bill'].currentBalance != 0:
                validated_data['bill'].currentBalance -= validated_data['amount']
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




