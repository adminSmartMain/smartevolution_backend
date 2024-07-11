# Rest Framework
from rest_framework import serializers
# Utils
from apps.report.api.models.pendingAccounts.index import PendingAccount
from django.utils import timezone
from apps.base.utils.index import gen_uuid
# Exceptions
from apps.base.exceptions import HttpException


class PendingAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = PendingAccount
        fields = '__all__'

    def create(self, validated_data):
        validated_data['id']              = gen_uuid()
        validated_data['created_at']      = timezone.now()
        validated_data['user_created_at'] = self.context['request'].user
        return  super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['user_updated_at'] = self.context['request'].user
        validated_data['updated_at']      = timezone.now()
        return super().update(instance, validated_data)
