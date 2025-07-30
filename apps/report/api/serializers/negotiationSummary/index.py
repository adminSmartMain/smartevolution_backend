# Rest Framework
from rest_framework import serializers
# Serializers
from apps.report.api.serializers.pendingAccount.index import PendingAccountSerializer
from apps.administration.api.serializers.emitterDeposit.index import EmitterDepositSerializer
from apps.administration.api.serializers.accountingControl.index import AccountingControlSerializer
# Utils
from apps.report.api.models.index import NegotiationSummary
from django.utils import timezone
from apps.base.utils.index import gen_uuid
# Exceptions
from apps.base.exceptions import HttpException

# Models 
from apps.report.api.models.pendingAccounts.index import PendingAccount
from apps.administration.api.models.emitterDeposit.index import EmitterDeposit
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
        validated_data['id'] = gen_uuid()
        validated_data['created_at'] = timezone.now()
        validated_data['user_created_at'] = self.context['request'].user
        # create the pending Accounts of the operation
        if 'pendingAccounts' in self.context['request'].data:
            for x in self.context['request'].data['pendingAccounts']:
                serializer = PendingAccountSerializer(data=x, context={'request': self.context['request']})
                if serializer.is_valid():
                    serializer.save()
        return NegotiationSummary.objects.create(**validated_data)

    def update(self, instance, validated_data):
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


class NegotiationSummaryReadOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = NegotiationSummary
        fields = '__all__'

    def to_representation(self, instance):
        #accountingControl = []
        data = super().to_representation(instance)
        logger.debug('si sale algo aqi es el fallo 1')
        data['pendingAccounts']  = PendingAccountSerializer(PendingAccount.objects.filter(opId=instance.opId), many=True).data

        logger.debug('si sale algo aqi es el fallo 2')
        data['emitterDeposits']  = EmitterDepositSerializer(EmitterDeposit.objects.filter(operation__opId=instance.opId), many=True).data
        logger.debug('si sale algo aqi es el fallo 3' )
        data['totalDeposits']    = sum([x['amount'] for x in data['emitterDeposits']]) if len(data['emitterDeposits']) > 0 else data['totalDeposits']
        data['pendingToDeposit'] = data['total'] - data['totalDeposits']  
        # get the account control of the emitter deposits
        #for x in data['emitterDeposits']:
            # get the account control of the emitter deposit
        #    accountingControlData = AccountingControlSerializer(AccountingControlSerializer.Meta.model.objects.get(emitterDeposit__id=x['id'])).data
        #    accountingControl.append(accountingControlData)
        #data['accountingControl'] = accountingControl
        return data
