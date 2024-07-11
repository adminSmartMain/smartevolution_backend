# Rest Framework
from rest_framework import serializers
# Models
from apps.bill.models import tempFile
# Utils
from datetime import datetime as dt
from apps.base.utils.index import gen_uuid, XMLBase64File


class TempFileSerializer(serializers.ModelSerializer):
    file = XMLBase64File()
    
    class Meta:
        model = tempFile
        fields = '__all__'
    
    def create(self, validated_data):
        return tempFile.objects.create(**validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)