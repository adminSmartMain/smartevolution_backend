# Rest Framework
from rest_framework import serializers
# Models
from apps.client.models import LegalRepresentative
# Utils
from django.utils import timezone
from apps.base.utils.index import gen_uuid


class LegalRepresentativeSerializer(serializers.ModelSerializer):
    department = serializers.CharField(source='city.department.id', read_only=True)
    class Meta:
        model = LegalRepresentative
        fields = "__all__"

    def create(self, validated_data):
        validated_data['id'] = gen_uuid()
        validated_data['created_at'] = timezone.now()
        validated_data['user_created_at'] = self.context['request'].user
        return LegalRepresentative.objects.create(**validated_data)
        

    def update(self, instance, validated_data):
        instance.updated_at = timezone.now()
        instance.user_updated_at = self.context['request'].user
        return super().update(instance, validated_data)