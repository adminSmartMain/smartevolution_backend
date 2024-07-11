# Rest Framework
from rest_framework import serializers
# Models
from apps.client.models    import Account, Client
from apps.operation.models import PreOperation
# Utils
from django.utils import timezone
from apps.base.utils.index import gen_uuid
# Exceptions
from apps.base.exceptions import HttpException


class AccountSerializer(serializers.ModelSerializer):
    
        class Meta:
            model  = Account
            fields = "__all__" 
    
        def create(self, validated_data):
            try:
                verify = Account.objects.filter(client=validated_data['client'])
                #if verify.count() == 2:
                #    raise HttpException(401, 'El cliente ya tiene dos cuentas')

                for account in verify:
                    if account.primary == True and validated_data['primary'] == True:
                        raise HttpException(400, 'El cliente ya tiene una cuenta primaria')

                validated_data['id'] = gen_uuid()
                validated_data['created_at'] = timezone.now()
                validated_data['user_created_at'] = self.context['request'].user
                account = Account.objects.create(**validated_data)
                return account
            except Exception as e:
                raise HttpException(500, str(e))
        
        def to_representation(self, instance):
            representation = super().to_representation(instance)
            # substract the amount of the pending operations
    
            # Get the pending operations
            pendingOperations = PreOperation.objects.filter(clientAccount=instance.id, status=0)
            # Get the amount of the pending operations
            if len(pendingOperations) > 0:
                amount = instance.balance
                for operation in pendingOperations:
                    amount -= operation.presentValueInvestor
                representation['balance'] = amount
            
            return representation   
    
        #def update(self, instance, validated_data):
        #    # check the risk profile balancesz
        #    try:
        #        # validate the risk profile balances
        #        riskProfile     = RiskProfileSerializer.Meta.model.objects.get(client=instance.client)
        #        # get the accounts of the clients
        #        accounts        = Account.objects.filter(client=instance.client)
#
        #        if len(accounts) == 1:
        #            # To obtain the capital available to allocate
        #            investor_balance = riskProfile.investor_balance - accounts[0].investor_balance
        #            emitter_balance  = riskProfile.emitter_balance  - accounts[0].emitter_balance
        #            payer_balance    = riskProfile.payer_balance    - accounts[0].payer_balance
        #            if 'investor_balance' in validated_data:
        #                if validated_data['investor_balance'] > investor_balance:
        #                    raise HttpException(400, 'investor balance exceeds the risk profile balance')
        #            if 'emitter_balance' in validated_data:
        #                if validated_data['emitter_balance'] > emitter_balance:
        #                    raise HttpException(400, 'emitter balance exceeds the risk profile balance')
        #            if 'payer_balance' in validated_data:
        #                if validated_data['payer_balance'] > payer_balance:
        #                    raise HttpException(400, 'payer balance exceeds the risk profile balance')
        #        else:
        #            # To obtain the capital available to allocate
        #            investor_balance = riskProfile.investor_balance - (accounts[0].investor_balance + accounts[1].investor_balance)
        #            emitter_balance  = riskProfile.emitter_balance  - (accounts[0].emitter_balance  + accounts[1].emitter_balance)
        #            payer_balance    = riskProfile.payer_balance    - (accounts[0].payer_balance    + accounts[1].payer_balance)
        #            if 'investor_balance' in validated_data:
        #                if validated_data['investor_balance'] > investor_balance:
        #                    raise HttpException(400, 'investor balance exceeds the risk profile balance')
        #            if 'emitter_balance' in validated_data:
        #                if validated_data['emitter_balance'] > emitter_balance:
        #                    raise HttpException(400, 'emitter balance exceeds the risk profile balance')
        #            if 'payer_balance' in validated_data:
        #                if validated_data['payer_balance'] > payer_balance:
        #                    raise HttpException(400, 'payer balance exceeds the risk profile balance')
        #        instance.updated_at = timezone.now()
        #        instance.user_updated_at = self.context['request'].user
        #        return super().update(instance, validated_data)
        #    except Exception as e:
        #        raise HttpException(500, str(e))

class AccountReadOnlySerializer(serializers.ModelSerializer):
    client = serializers.SerializerMethodField(method_name='get_client')
    class Meta:
            model  = Account
            fields = "__all__"

    def get_client(self, obj):
        return {
            'id': obj.client.id,
            'document': obj.client.document_number,
            'name': obj.client.social_reason if obj.client.social_reason else obj.client.first_name + ' ' + obj.client.last_name
        }
    
