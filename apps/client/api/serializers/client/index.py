# Rest Framework
from rest_framework import serializers
# Models
from apps.client.models import Client, RiskProfile, FinancialProfile, Contact, LegalRepresentative
# Serializers
from apps.authentication.api.serializers.user.index import UserReadOnlySerializer , UserSerializer
from apps.client.api.serializers.riskProfile.index import RiskProfileSerializer
from apps.client.api.serializers.contact.index import ContactSerializer
from apps.client.api.serializers.legalRepresentative.index import LegalRepresentativeSerializer
from apps.client.api.serializers.request.index import RequestSerializer
from apps.client.api.serializers.account.index import AccountSerializer
from apps.misc.api.serializers.index import (
    TypeClientSerializer, CountrySerializer, TypeIdentitySerializer, CityReadOnlySerializer, DepartmentSerializer,
    CIIUReadOnlySerializer, AccountTypeSerializer
)
# Utils
from django.utils import timezone
from apps.base.utils.index import gen_uuid, PDFBase64File, genAccountNumber


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = "__all__"

    def create(self, validated_data):
        validated_data['id'] = gen_uuid()
        validated_data['created_at'] = timezone.now()
        validated_data['user_created_at'] = self.context['request'].user
        return Client.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.updated_at = timezone.now()
        instance.user_updated_at = self.context['request'].user
        return super().update(instance, validated_data)

class ClientReadOnlySerializer(serializers.ModelSerializer):
    riskProfile       = serializers.SerializerMethodField(method_name='validateRiskProfile')
    financial_profile = serializers.SerializerMethodField(method_name='get_financial_profile')
    entered_by        = UserReadOnlySerializer(read_only=True)
    class Meta:
        model = Client
        fields = "__all__"

    def validateRiskProfile(self,obj):
        try:
            risk_profile = RiskProfile.objects.get(client=obj)
            return True
        except RiskProfile.DoesNotExist:
            return False
    
    def get_financial_profile(self,obj):
        try:
            financial_profile = FinancialProfile.objects.filter(client=obj)
            if len(financial_profile) > 0:
                return True
            return False
        except FinancialProfile.DoesNotExist:
            return False

class ClientByIdSerializer(serializers.ModelSerializer):
    contacts             = serializers.SerializerMethodField(method_name='get_contacts')
    legal_representative = serializers.SerializerMethodField(method_name='get_legal_representative')
    entered_by           = UserReadOnlySerializer(read_only=True)
    riskProfile          = serializers.SerializerMethodField(method_name='get_risk_profile')

    class Meta:
        model  = Client
        fields = "__all__"

    
    def get_contacts(self, obj):
        try:
            contacts   = Contact.objects.filter(client=obj)
            serializer = ContactSerializer(contacts, many=True)
            return serializer.data
        except Exception as e:
            return None
    
    def get_legal_representative(self, obj):
        try:
            legal_representative = LegalRepresentative.objects.filter(client=obj)
            serializer           = LegalRepresentativeSerializer(legal_representative, many=True)
            return serializer.data[0]
        except Exception as e:
            return None
    
    def get_risk_profile(self, obj):
        try:
            risk_profile = RiskProfile.objects.get(client=obj)
            serializer   = RiskProfileSerializer(risk_profile)
            return serializer.data
        except RiskProfile.DoesNotExist:
            return None

