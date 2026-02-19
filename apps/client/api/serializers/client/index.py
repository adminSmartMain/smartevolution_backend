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
from django.core.exceptions import ValidationError

# Utils
from django.utils import timezone
from apps.base.utils.index import gen_uuid, PDFBase64File, genAccountNumber
from apps.client.api.serializers.riskProfile.index import RiskProfileReadOnlySerializer
from apps.client.api.models.client.index import ClientRole, ClientRoleAssignment
from rest_framework import serializers
from django.conf import settings
from apps.client.models import Client
from apps.base.utils.index import gen_uuid  # o tu gen_uuid
from apps.base.utils.index import gen_uuid, PDFBase64File, uploadFileBase64 # ajusta import real
import logging
import base64
import re
from django.conf import settings
from rest_framework import serializers
logger = logging.getLogger(__name__)



ALLOWED_MIME = {"image/jpeg", "image/png"}
MAX_BYTES = 2 * 1024 * 1024  # 2MB

def parse_data_url(data_url: str):
    """
    data:image/png;base64,AAAA...
    -> (mime, raw_base64)
    """
    m = re.match(r"^data:(.*?);base64,(.*)$", data_url or "")
    if not m:
        return None, None
    return m.group(1), m.group(2)

def validate_image_data_url(data_url: str):
    mime, b64 = parse_data_url(data_url)
    if not mime or not b64:
        raise serializers.ValidationError("Imagen inválida (base64/dataURL).")

    if mime not in ALLOWED_MIME:
        raise serializers.ValidationError("Solo JPG o PNG.")

    try:
        raw = base64.b64decode(b64, validate=True)
    except Exception:
        raise serializers.ValidationError("Base64 inválido.")

    if len(raw) > MAX_BYTES:
        raise serializers.ValidationError("Máximo 2MB.")
class ClientRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientRole
        fields = "__all__"
        
    def create(self, validated_data):
        validated_data['id'] = gen_uuid()
        validated_data['created_at'] = timezone.now()
        validated_data['user_created_at'] = self.context['request'].user
        risk_profile = ClientRole.objects.create(**validated_data)
        return risk_profile  
    
    
class ClientRoleMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientRole
        fields = ["id", "code", "name"]


# -------------------------
# Assignment (tabla puente)
# -------------------------

class ClientRoleAssignmentReadSerializer(serializers.ModelSerializer):
    role = ClientRoleMiniSerializer(read_only=True)

    class Meta:
        model = ClientRoleAssignment
        fields = ["id", "role", "notes", "created_at"]


class ClientRoleAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientRoleAssignment
        fields = "__all__"

class ClientSerializer(serializers.ModelSerializer):
    # este campo recibirá el dataURL (string)
    profile_image = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = Client
        fields = "__all__"

    def create(self, validated_data):
        try:
            validated_data["id"] = gen_uuid()
            validated_data["user_created_at"] = self.context["request"].user

            img = validated_data.get("profile_image")
            if img:
                validate_image_data_url(img)
                key = uploadFileBase64(
                    files_bse64=[img],
                    file_path=f"clients-profiles/{validated_data['id']}"
                )
                validated_data["profile_image"] = (
                    f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{key}"
                )

            return Client.objects.create(**validated_data)

        except Exception as e:
            logger.error(f"Error al crear cliente (avatar): {str(e)}")
            raise serializers.ValidationError(f"Error al crear cliente: {str(e)}")

    def update(self, instance, validated_data):
        try:
            # Si viene vacío, NO lo borres (a menos que tú quieras permitir borrar)
            img = validated_data.get("profile_image", None)

            if img:
                # si ya viene un URL (no base64), lo dejamos tal cual
                if isinstance(img, str) and img.startswith("http"):
                    instance.profile_image = img
                else:
                    validate_image_data_url(img)
                    key = uploadFileBase64(
                        files_bse64=[img],
                        file_path=f"clients-profiles/{instance.id}"
                    )
                    instance.profile_image = (
                        f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{key}"
                    )

            # resto de campos normales
            for k, v in validated_data.items():
                if k == "profile_image":
                    continue
                setattr(instance, k, v)

            instance.save()
            return instance

        except Exception as e:
            logger.error(f"Error al actualizar cliente (avatar): {str(e)}")
            raise serializers.ValidationError(f"Error al actualizar cliente: {str(e)}")



class ClientReadOnlySerializer(serializers.ModelSerializer):
    RegisteredAt = serializers.DateTimeField(read_only=True, required=False, allow_null=True)
    LastOperationAt = serializers.DateTimeField(read_only=True, required=False, allow_null=True)

    InvoicesTotal = serializers.IntegerField(read_only=True, required=False)
    InvoicesPending = serializers.IntegerField(read_only=True, required=False)

    # ✅ NUEVOS (annotate)
    SaldoCuenta = serializers.DecimalField(max_digits=20, decimal_places=2, read_only=True, required=False)
    PorCobrar = serializers.DecimalField(max_digits=20, decimal_places=2, read_only=True, required=False)
    IsInvestor = serializers.BooleanField(read_only=True, required=False)
    TotalPortafolio = serializers.DecimalField(max_digits=20, decimal_places=2, read_only=True, required=False)

    riskProfile = serializers.SerializerMethodField(method_name='validateRiskProfile')
    financial_profile = serializers.SerializerMethodField(method_name='get_financial_profile')
    riskProfileData = serializers.SerializerMethodField(method_name="get_risk_profile_data")
    entered_by = UserReadOnlySerializer(read_only=True)
    rolesData = serializers.SerializerMethodField(method_name="get_roles_data")
    rolesLabel = serializers.SerializerMethodField(method_name="get_roles_label")
    class Meta:
        model = Client
        fields = "__all__"

    def get_roles_data(self, obj):
        qs = obj.role_assignments.select_related("role").all()
        return ClientRoleAssignmentReadSerializer(qs, many=True).data

    def get_roles_label(self, obj):
        names = obj.role_assignments.select_related("role").values_list("role__name", flat=True)
        return ", ".join(list(names)) if names else ""
    
    def validateRiskProfile(self,obj):
        try:
            risk_profile = RiskProfile.objects.get(client=obj)
            return True
        except RiskProfile.DoesNotExist:
            return False
        
    def get_risk_profile_data(self, obj):
        # Si NO existe, retorna None
        rp = RiskProfile.objects.filter(client=obj).select_related("bank", "account_type").first()
        return RiskProfileReadOnlySerializer(rp).data if rp else None
    
    def get_financial_profile(self,obj):
        try:
            financial_profile = FinancialProfile.objects.filter(client=obj)
            if len(financial_profile) > 0:
                return True
            return False
        except FinancialProfile.DoesNotExist:
            return False
    def get_roles_data(self, obj):
        # gracias al related_name="role_assignments"
        qs = obj.role_assignments.select_related("role").all()
        return ClientRoleAssignmentReadSerializer(qs, many=True).data

    def get_roles_label(self, obj):
        # "Emisor, Inversionista" (ideal para una columna)
        roles = obj.role_assignments.select_related("role").values_list("role__name", flat=True)
        return ", ".join(list(roles)) if roles else ""
    
    
class ClientByIdSerializer(serializers.ModelSerializer):
    contacts             = serializers.SerializerMethodField(method_name='get_contacts')
    legal_representative = serializers.SerializerMethodField(method_name='get_legal_representative')
    entered_by           = UserReadOnlySerializer(read_only=True)
    riskProfile          = serializers.SerializerMethodField(method_name='get_risk_profile')

    # ✅ ROLES
    rolesData  = serializers.SerializerMethodField(method_name="get_roles_data")
    rolesLabel = serializers.SerializerMethodField(method_name="get_roles_label")

    class Meta:
        model  = Client
        fields = "__all__"

    def get_roles_data(self, obj):
        qs = obj.role_assignments.select_related("role").all()
        return ClientRoleAssignmentReadSerializer(qs, many=True).data

    def get_roles_label(self, obj):
        roles = obj.role_assignments.select_related("role").values_list("role__name", flat=True)
        return ", ".join(list(roles)) if roles else ""

    def get_contacts(self, obj):
        try:
            contacts = Contact.objects.filter(client=obj)
            serializer = ContactSerializer(contacts, many=True)
            return serializer.data
        except Exception:
            return None

    def get_legal_representative(self, obj):
        try:
            legal_representative = LegalRepresentative.objects.filter(client=obj)
            serializer = LegalRepresentativeSerializer(legal_representative, many=True)
            return serializer.data[0] if serializer.data else None
        except Exception:
            return None

    def get_risk_profile(self, obj):
        try:
            risk_profile = RiskProfile.objects.get(client=obj)
            serializer = RiskProfileSerializer(risk_profile)
            return serializer.data
        except RiskProfile.DoesNotExist:
            return None
