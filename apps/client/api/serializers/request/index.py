# Rest Framework
from rest_framework import serializers
# Models
from apps.client.models import Request
# Utils
from django.utils import timezone
from apps.base.utils.index import gen_uuid
# Exceptions
from apps.base.exceptions import HttpException

class RequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = Request
        fields = "__all__" 

    def create(self, validated_data):
        try:
            validated_data['id'] = gen_uuid()
            validated_data['created_at'] = timezone.now()
            validated_data['user_created_at'] = self.context['request'].user
            return Request.objects.create(**validated_data)
        except Exception as e:
            raise HttpException(400, str(e))

    def update(self, instance, validated_data):
        instance.updated_at = timezone.now()
        instance.user_updated_at = self.context['request'].user
        return super().update(instance, validated_data)