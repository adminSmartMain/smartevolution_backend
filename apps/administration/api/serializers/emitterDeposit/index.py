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
from apps.operation.utils.penny_allocation import as_decimal, round_cop
from apps.report.models import NegotiationSummary


class EmitterDepositSerializer(serializers.ModelSerializer):
    class Meta:
        model  = EmitterDeposit
        fields = "__all__"

    def validate_amount(self, value):
        amount = as_decimal(value)
        if amount != round_cop(amount):
            raise serializers.ValidationError('El desembolso COP debe ser un valor entero, sin centavos.')
        if amount <= 0:
            raise serializers.ValidationError('El desembolso debe ser mayor que cero.')
        # Keep the legacy float column integer-valued while consumers migrate to
        # settledAmount, which is the authoritative decimal representation.
        return float(amount)

    def validate(self, attrs):
        operation = attrs.get('operation', getattr(self.instance, 'operation', None))
        amount = attrs.get('amount', getattr(self.instance, 'amount', None))
        if not operation or amount is None:
            return attrs

        summary = NegotiationSummary.objects.filter(opId=operation.opId).first()
        if not summary:
            return attrs

        deposits = EmitterDeposit.objects.filter(operation__opId=operation.opId, state=True)
        if self.instance:
            deposits = deposits.exclude(pk=self.instance.pk)
        already_assigned = sum(
            (as_decimal(deposit.settledAmount if deposit.settledAmount is not None else deposit.amount) for deposit in deposits),
            as_decimal(0),
        )
        total_to_disburse = as_decimal(
            summary.settledTotal if summary.settledTotal is not None else summary.total
        ) - as_decimal(getattr(summary, 'manualAdjustment', 0))
        if already_assigned + as_decimal(amount) > total_to_disburse:
            raise serializers.ValidationError({
                'amount': 'El desembolso supera el saldo disponible de la operación.'
            })
        return attrs
    
    def create(self, validated_data):
        # validate amount of the deposit is lesser than the amount of the operation
        # TODO: validate the amount of the deposit is lesser than the amount of the operation when the operation view is created
        #if validated_data['amount'] > validated_data['operation'].amount:
        #    raise HttpException(400, 'El monto del giro no puede ser mayor al monto de la operación')
        validated_data['id'] = gen_uuid()
        validated_data['created_at'] = timezone.now()
        validated_data['user_created_at'] = self.context['request'].user
        validated_data['settledAmount'] = round_cop(validated_data['amount'])

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
        if validated_data.get('operation'):
            self._sync_summary_balance(validated_data['operation'].opId)
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
        if 'amount' in validated_data:
            validated_data['settledAmount'] = round_cop(validated_data['amount'])
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
        updated = super().update(instance, validated_data)
        if updated.operation:
            self._sync_summary_balance(updated.operation.opId)
        return updated

    @staticmethod
    def _sync_summary_balance(op_id):
        summary = NegotiationSummary.objects.filter(opId=op_id).first()
        if not summary:
            return
        total_deposits = sum(
            (as_decimal(deposit.settledAmount if deposit.settledAmount is not None else deposit.amount)
             for deposit in EmitterDeposit.objects.filter(operation__opId=op_id, state=True)),
            as_decimal(0),
        )
        total = as_decimal(summary.settledTotal if summary.settledTotal is not None else summary.total)
        adjustment = as_decimal(getattr(summary, 'manualAdjustment', 0))
        pending = round_cop(total - total_deposits - adjustment)
        summary.totalDeposits = int(total_deposits)
        summary.pendingToDeposit = int(pending)
        summary.settledPendingToDeposit = pending
        summary.save(update_fields=['totalDeposits', 'pendingToDeposit', 'settledPendingToDeposit', 'updated_at'])



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
