# Rest Framework
from rest_framework import serializers
# Models
from apps.administration.models import EmitterDeposit, AccountingControl
# Serializers
from apps.administration.api.serializers.accountingControl.index import AccountingControlSerializer
from apps.client.api.serializers.client.index import ClientSerializer
from apps.misc.api.serializers.index import BankSerializer, AccountTypeSerializer
# Utils
from django.utils import timezone
from apps.base.utils.index import gen_uuid
# Exceptions
from apps.base.exceptions import HttpException


class EmitterDepositSerializer(serializers.ModelSerializer):
    class Meta:
        model  = EmitterDeposit
        fields = "__all__"
    
    def create(self, validated_data):
        # validate amount of the deposit is lesser than the amount of the operation
        # TODO: validate the amount of the deposit is lesser than the amount of the operation when the operation view is created
        #if validated_data['amount'] > validated_data['operation'].amount:
        #    raise HttpException(400, 'El monto del giro no puede ser mayor al monto de la operación')
        validated_data['id'] = gen_uuid()
        validated_data['created_at'] = timezone.now()
        validated_data['user_created_at'] = self.context['request'].user

        # get the last deposit id
        try:
            last_deposit = EmitterDeposit.objects.all().order_by('-edId').first()
            if last_deposit.edId != None:
                validated_data['edId'] = last_deposit.edId + 1
        except EmitterDeposit.DoesNotExist:
            validated_data['edId'] = 1
        except Exception as e:
            validated_data['edId'] = 1

        # create the deposit
        EmitterDeposit.objects.create(**validated_data)
        # Create the accounting control for the deposit
        
        if self.context['request'].data['account'] != None:  
            accountingControlData = {
                'account'        : self.context['request'].data['account'],
                'type'           : self.context['request'].data['egressType'],
                'observations'   : self.context['request'].data['observations'],
                'emitterDeposit' : validated_data['id']
            }
            accountingControl = AccountingControlSerializer(data=accountingControlData, context={'request': self.context['request']})
            if accountingControl.is_valid():
                accountingControl.save() 
            else:
                raise HttpException(400, accountingControl.errors)
        # save the deposit
        return validated_data

    def update(self, instance, validated_data):
        instance.updated_at      = timezone.now()
        instance.user_updated_at = self.context['request'].user
        # update the accounting control for the deposit
        if self.context['request'].data['account'] != None:
            try:
                getAccountingControl = AccountingControl.objects.get(emitterDeposit_id=instance.id)
                accountingControlData = {
                    'account'        : self.context['request'].data['account'] if self.context['request'].data['account'] != None else accountingControl.account,
                    'type'           : self.context['request'].data['egressType'] if self.context['request'].data['egressType'] != None else accountingControl.type,
                    'observations'   : self.context['request'].data['observations'] if self.context['request'].data['observations'] != None  else "",
                    'emitterDeposit' : instance.id
                }
            except:
                accountingControlData = {
                    'account'        : self.context['request'].data['account'] if self.context['request'].data['account'] != None else None,
                    'type'           : self.context['request'].data['egressType'] if self.context['request'].data['egressType'] != None else None ,
                    'observations'   : self.context['request'].data['observations'] if self.context['request'].data['observations'] != None else "",
                    'emitterDeposit' : instance.id
                }
                accountingControl = AccountingControlSerializer(data=accountingControlData, context={'request': self.context['request']})
                if accountingControl.is_valid():
                    accountingControl.save() 
                else:
                    raise HttpException(400, accountingControl.errors)
            serializer = AccountingControlSerializer(getAccountingControl, data=accountingControlData, context={'request': self.context['request']}, partial=True)
            if serializer.is_valid():
                serializer.save()
            else:
                raise HttpException(400, serializer.errors)
        return super().update(instance, validated_data)



class EmitterDepositReadOnlySerializer(serializers.ModelSerializer):
    client = ClientSerializer(read_only=True)
    accountingControl = serializers.SerializerMethodField(method_name='get_accounting_control')
    class Meta:
        model  = EmitterDeposit
        fields = "__all__"

    def get_accounting_control(self, obj):
        try:
            accountingControl = AccountingControl.objects.get(emitterDeposit_id=obj.id)
            serializer = AccountingControlSerializer(accountingControl)
            return serializer.data
        except AccountingControl.DoesNotExist:
            return None
        except Exception as e:
            return None


class EmitterDepositNSSerializer(serializers.ModelSerializer):
    bank   = BankSerializer(read_only=True)
    accountingControls = serializers.SerializerMethodField(method_name='get_accounting_controls')
    class Meta:
        model  = EmitterDeposit
        fields = "__all__"

    def get_accounting_controls(self, obj):
        try:
            accountingControls = AccountingControl.objects.filter(emitterDeposit_id=obj.id)
            serializer = AccountingControlSerializer(accountingControls, many=True)
            return serializer.data
        except AccountingControl.DoesNotExist:
            return None
        except Exception as e:
            return None