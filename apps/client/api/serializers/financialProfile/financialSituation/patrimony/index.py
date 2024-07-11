# Rest Framework
from rest_framework import serializers
# Models
from apps.client.models import Patrimony
# Utils
from datetime import datetime as dt
from apps.base.utils.index import gen_uuid


class PatrimonySerializer(serializers.ModelSerializer):
    class Meta:
        model = Patrimony
        fields = "__all__"

    def create(self, validated_data):
        validated_data['id'] = gen_uuid()
        validated_data['user_created_at'] = self.context['request'].user
        assets = Patrimony.objects.create(**validated_data)
        return assets

    def update(self, instance, validated_data):
        instance.updated_at = dt.now()
        instance.user_updated_at = self.context['request'].user
        return super().update(instance, validated_data)
