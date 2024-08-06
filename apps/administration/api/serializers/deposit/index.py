# Rest Framework
from rest_framework import serializers
# Models
from apps.administration.models import Deposit
# serializers
from apps.client.api.serializers.index import AccountSerializer, ClientSerializer
# Utils
from django.utils import timezone
from apps.base.utils.index import gen_uuid
# Exceptions
from apps.base.exceptions import HttpException
#utils
from apps.base.utils.logBalanceAccount import log_balance_change


class DepositSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Deposit
        fields = "__all__"
    
    def create(self, validated_data):            
        validated_data['id'] = gen_uuid()
        validated_data['created_at'] = timezone.now()
        validated_data['user_created_at'] = None
        # get the last deposit id
        try:
            last_deposit = Deposit.objects.all().order_by('-dId').first()
            if last_deposit.dId != None:
                validated_data['dId'] = last_deposit.dId + 1
        except:
            validated_data['dId'] = 1

        # update account balance
        validated_data['account'].balance += validated_data['amount']
        log_balance_change(validated_data['account'], 0, validated_data['account'].balance, validated_data['amount'], 'deposit', validated_data['id'], 'DepositSerializer - create')
        validated_data['account'].save()

        return Deposit.objects.create(**validated_data)

    def update(self, instance, validated_data):
        #check if the account is the same
        if instance.account.id != validated_data['account'].id:
            log_balance_change(instance.account, instance.account.balance, (instance.account.balance - instance.amount), -instance.amount, 'deposit', instance.id, 'DepositSerializer - update')
            instance.account.balance -= instance.amount
            instance.account.save()

            # update the new account balance
            log_balance_change(validated_data['account'], validated_data['account'].balance, (validated_data['account'].balance + validated_data['amount']), validated_data['amount'], 'deposit', instance.id, 'DepositSerializer - update')
            validated_data['account'].balance += validated_data['amount']

            validated_data['account'].save()
        else:
            # update account balance
            log_balance_change(instance.account, instance.account.balance, (instance.account.balance - instance.amount), -instance.amount, 'deposit', instance.id, 'DepositSerializer - update')
            instance.account.balance -= instance.amount
            log_balance_change(instance.account, instance.account.balance, (instance.account.balance + validated_data['amount']), validated_data['amount'], 'deposit', instance.id, 'DepositSerializer - update')
            instance.account.balance += validated_data['amount']
            instance.account.save()
        
        instance.updated_at = timezone.now()
        instance.user_updated_at = self.context['request'].user
        return super().update(instance, validated_data)


class DepositReadOnlySerializer(serializers.ModelSerializer):
    client  = ClientSerializer(read_only=True)
    class Meta:
        model  = Deposit
        fields = "__all__"

class DepositReportSerializer(serializers.ModelSerializer):
    client  = ClientSerializer(read_only=True)
    account = AccountSerializer(read_only=True)
    class Meta:
        model  = Deposit
        fields = "__all__"