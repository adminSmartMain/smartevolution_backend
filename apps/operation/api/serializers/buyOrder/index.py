# Rest Framework
from rest_framework import serializers
# Utils
from apps.operation.models import BuyOrder
from django.utils import timezone
from apps.base.utils.index import gen_uuid
# Serializers
from apps.operation.api.serializers.index import PreOperationSerializer
# Exceptions
from apps.base.exceptions import HttpException


class BuyOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuyOrder
        fields = '__all__'

    def create(self, validated_data):
        validated_data['id']              = gen_uuid()
        validated_data['created_at']      = timezone.now()
        validated_data['user_created_at'] = None
        return  super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['user_updated_at'] = None
        validated_data['updated_at']      = timezone.now()
        return super().update(instance, validated_data)


class BuyOrderReadOnlySerializer(serializers.ModelSerializer):
    operation = PreOperationSerializer(read_only=True)
    class Meta:
        model = BuyOrder
        fields = '__all__'