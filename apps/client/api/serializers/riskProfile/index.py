# Rest Framework
from rest_framework import serializers
# Models
from apps.client.models import RiskProfile, Client
# Utils
from django.utils import timezone
from apps.base.utils.index import gen_uuid

class RiskProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskProfile
        fields = '__all__'

    def create(self, validated_data):
        validated_data['id'] = gen_uuid()
        validated_data['created_at'] = timezone.now()
        validated_data['user_created_at'] = self.context['request'].user
        risk_profile = RiskProfile.objects.create(**validated_data)

        return risk_profile
    
    def update(self, instance, validated_data):
        instance.updated_at = timezone.now()
        instance.user_updated_at = self.context['request'].user
        return super().update(instance, validated_data)

class RiskProfileReadOnlySerializer(serializers.ModelSerializer):
    client = serializers.SerializerMethodField(method_name='get_client')
    class Meta:
        model = RiskProfile
        fields = '__all__'

    def create(self, validated_data):
        validated_data['id'] = gen_uuid()
        validated_data['created_at'] = timezone.now()
        validated_data['user_created_at'] = self.context['request'].user
        risk_profile = RiskProfile.objects.create(**validated_data)

        return risk_profile
    
    def update(self, instance, validated_data):
        instance.updated_at = timezone.now()
        instance.user_updated_at = self.context['request'].user
        return super().update(instance, validated_data)

    def get_client(self, obj):
        if obj.client.social_reason:
            return obj.client.social_reason
        else:
            return obj.client.first_name + ' ' + obj.client.last_name