# Rest Framework
from rest_framework import serializers
# Models
from apps.client.models import Assets
# Utils
from datetime import datetime as dt
from apps.base.utils.index import gen_uuid

class AssetsSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Assets
        fields = "__all__"
    
    def create(self, validated_data):
        validated_data['id'] = gen_uuid()
        validated_data['user_created_at'] = self.context['request'].user
        assets = Assets.objects.create(**validated_data)
        return assets
    
    def update(self, instance, validated_data):
        instance.updated_at      = dt.now()
        instance.user_updated_at = self.context['request'].user
        return super().update(instance, validated_data)