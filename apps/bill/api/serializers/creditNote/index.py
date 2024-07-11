# Rest Framework
from rest_framework import serializers
# Models
from apps.bill.models import CreditNote
# Utils
from datetime import datetime as dt
from apps.base.utils.index import gen_uuid
# Exceptions
from apps.base.exceptions import HttpException


class CreditNoteSerializer(serializers.ModelSerializer):
    
        class Meta:
            model = CreditNote
            fields = '__all__'
        
        def create(self, validated_data):
            try:
                validated_data['id'] = gen_uuid()
                validated_data['user_created_at'] = self.context['request'].user
                return CreditNote.objects.create(**validated_data)
            except Exception as e:
                raise HttpException(500, e)
    
        def update(self, instance, validated_data):
            instance.updated_at = dt.now()
            instance.user_updated_at = self.context['request'].user
            return super().update(instance, validated_data)