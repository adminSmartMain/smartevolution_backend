# Rest Framework
from rest_framework import serializers
# Models
from apps.bill.models import BillEvent
# Utils
from datetime import datetime as dt
from apps.base.utils.index import gen_uuid


class BillEventSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = BillEvent
        fields = '__all__'
    
    def create(self, validated_data):
        validated_data['id'] = gen_uuid()
        validated_data['user_created_at'] = self.context['request'].user.id
        return BillEvent.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.updated_at = dt.now()
        instance.user_updated_at = self.context['request'].user
        return super().update(instance, validated_data)