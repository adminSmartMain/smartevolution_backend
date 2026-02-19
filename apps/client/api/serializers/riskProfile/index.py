# Rest Framework
from rest_framework import serializers
# Models
from apps.client.models import RiskProfile, Client
# Utils
from django.utils import timezone
from apps.base.utils.index import gen_uuid
from rest_framework import serializers
from apps.client.api.models.riskProfile.index import LevelRisk

from rest_framework import serializers
from django.utils import timezone


# from .utils import gen_uuid  # si lo usas

class RiskProfileSerializer(serializers.ModelSerializer):
    # devuelve el objeto completo
    riskLevelData = serializers.SerializerMethodField()

    class Meta:
        model = RiskProfile
        fields = "__all__"  # incluye riskLevels (id) + riskLevelData
        # o explícito si prefieres:
        # fields = [..., "riskLevels", "riskLevelData"]

    def get_riskLevelData(self, obj):
        return LevelRiskReadSerializer(obj.riskLevels).data if obj.riskLevels else None

    def create(self, validated_data):
        validated_data["id"] = gen_uuid()
        validated_data["created_at"] = timezone.now()
        validated_data["user_created_at"] = self.context["request"].user
        return RiskProfile.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.updated_at = timezone.now()
        instance.user_updated_at = self.context["request"].user
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
        


class LevelRiskSerializer(serializers.ModelSerializer):
    class Meta:
        model = LevelRisk
        fields = '__all__'
        
    def create(self, validated_data):
        validated_data['id'] = gen_uuid()
        validated_data['created_at'] = timezone.now()
        validated_data['user_created_at'] = self.context['request'].user
        risk_profile = LevelRisk.objects.create(**validated_data)

        return risk_profile  
    def validate(self, attrs):
        min_s = attrs.get("min_score", 0)
        max_s = attrs.get("max_score", 0)
        if min_s > max_s:
            raise serializers.ValidationError("min_score no puede ser mayor que max_score.")
        return attrs

class LevelRiskReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = LevelRisk
        fields = ["id", "min_score", "max_score", "level", "interpretation", "created_at"]
        read_only_fields = ["id", "created_at"]
