# Rest Framework
from rest_framework import serializers

# Models
from apps.report.api.models.index import SellOrder

# Utils
from apps.base.utils.index import gen_uuid, PDFBase64File
from django.utils import timezone

class SellOrderSerializer(serializers.ModelSerializer):
    file = PDFBase64File()

    class Meta:
        model = SellOrder
        fields = "__all__"

    def create(self, validated_data):
        validated_data['id'] = gen_uuid()
        validated_data['created_at'] = timezone.now()
        validated_data['user_created_at'] = self.context['request'].user
        SellOrder.objects.create(**validated_data)        
        return validated_data
