# Rest Framework
from rest_framework import serializers
# Models
from apps.administration.models import Refund
# Utils
from django.utils import timezone
from apps.base.utils.index import gen_uuid
# Exceptions
from apps.base.exceptions import HttpException
# Serializers
from apps.misc.api.serializers.index   import BankSerializer, AccountTypeSerializer
from apps.client.api.serializers.index import ClientSerializer, AccountSerializer


class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Refund
        fields = "__all__"
    
    def create(self, validated_data):            
        validated_data['id'] = gen_uuid()
        validated_data['created_at'] = timezone.now()
        validated_data['user_created_at'] = self.context['request'].user
        # validate account amount
        #if validated_data['account'].balance < (validated_data['amount'] + validated_data['gmAmount']):
        #    raise HttpException(400, 'El monto del reintegro no puede ser mayor al saldo de la cuenta')
        # substract amount from account
        validated_data['account'].balance -= validated_data['amount'] + validated_data['gmAmount']
        validated_data['account'].save()

        # get the last refund id
        try:
            last_refund = Refund.objects.all().order_by('-rId').first()
            if last_refund.rId != None:
                validated_data['rId'] = last_refund.rId + 1
        except:
            validated_data['rId'] = 1

        return Refund.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.updated_at      = timezone.now()
        instance.user_updated_at = self.context['request'].user
        if instance.amount != validated_data['amount'] or instance.gmAmount != validated_data['gmAmount']:
            # validate account amount
            if instance.account.balance < (validated_data['amount'] + validated_data['gmAmount']):
                raise HttpException(400, 'El monto del reintegro no puede ser mayor al saldo de la cuenta')
            # update account amount
            instance.account.balance += (instance.amount + instance.gmAmount)
            instance.account.balance -= validated_data['amount'] + validated_data['gmAmount']
            instance.account.save()

        return super().update(instance, validated_data)

class RefundReadOnlySerializer(serializers.ModelSerializer):
    client        = ClientSerializer()
    account       = AccountSerializer()
    bank          = BankSerializer()
    accountType   = AccountTypeSerializer()

    class Meta:
        model  = Refund
        fields = "__all__"