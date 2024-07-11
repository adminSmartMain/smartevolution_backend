# Rest Framework
from rest_framework import serializers
# Models
from apps.misc.models import TypeReceipt
# Utils
from django.utils import timezone
from apps.base.utils.index import gen_uuid
# Exceptions
from apps.base.exceptions import HttpException

class TypeReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeReceipt
        fields = "__all__"


    def create(self, validated_data):
        validated_data['id']              = gen_uuid()
        validated_data['created_at']      = timezone.now()
        validated_data['user_created_at'] = self.context['request'].user
        return TypeReceipt.objects.create(**validated_data)

    def update(self, instance, validated_data):
        if ('description' in validated_data):
            if len(validated_data['description']) < 3:
                raise HttpException(400, 'The description must have at least 3 characters.')

        instance.updated_at = timezone.now()
        instance.user_updated_at = self.context['request'].user

        return super().update(instance, validated_data)