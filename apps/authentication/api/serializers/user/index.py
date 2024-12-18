# Django
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
# Rest Framework
from rest_framework import serializers
# Models
from apps.authentication.api.models.user.index import User
from apps.authentication.api.models.userRole.index import UserRole
from rest_framework.authtoken.models import Token
# Utils
from django.utils import timezone
from apps.base.utils.index import gen_uuid, generatePassword, sendWhatsApp, sendEmail
# Exceptions
from apps.base.exceptions import HttpException
from rest_framework.exceptions import ValidationError

class UserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(style={'input_type': 'text'}, write_only=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name','email','role', 'description', 'phone_number']
        extra_kwargs = {
            'email'     : {'required': True},
            'first_name': {'required': True},
            'last_name' : {'required': True},
            'role'      : {'required': True},
        }

    def save(self):
        password = generatePassword(12)
        code     = generatePassword(12) 
        if User.objects.filter(email=self.validated_data['email']).exists():
            raise HttpException(400, 'El correo ya se encuentra registrado')
        
        description = ""
        if 'description' in self.validated_data:
            description = self.validated_data['description'] if 'description' in self.validated_data else self.context['request'].data['social_reason']

        # validate if password is not registered yet
        validateCode = False
        while validateCode:
            if User.objects.filter(code=code).exists():
                code = generatePassword(12)
            else:
                validateCode = True

        account = User(id=gen_uuid(),email=self.validated_data['email'],first_name=self.validated_data['first_name'],
                        last_name=self.validated_data['last_name'], description=description,phone_number=self.validated_data['phone_number'],
                        code=code)
        account.set_password(code)
        account.save()
        user = User.objects.get(id=account.id)
        try:
            role = UserRole.objects.create(id=gen_uuid(),user_id=user.id, role_id=self.validated_data['role'])
            role.save()
            if self.validated_data['role'] == '5da6b88d-c248-4840-815a-bed2dce6af50' or self.validated_data['role'] == '2f4aadaa-df75-408b-9d07-111c7ab4a042':
                sendEmail('Credencial de acceso', f'Hola {user.first_name if user.first_name else user.description}, te damos la bienvenida a smart evolution esta es tu contraseña:{code} ',user.email)
            #sendWhatsApp(f'Hola {user.first_name if user.first_name else user.description}, te damos la bienvenida a smart evolution  '
            #            + f'este es tu codigo de acceso - {code}', user.phone_number)
            return user
        except Exception as e:
            if user:
                user.delete()
            raise HttpException(500, str(e))


class UserReadOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['id', 'first_name', 'last_name', 'email']
        read_only_fields = ['id', 'first_name', 'last_name', 'email']

class UpdateUserSerializer(serializers.ModelSerializer):
    old_password     = serializers.CharField(style={'input_type': 'password'}, write_only=True, required=False)
    new_password     = serializers.CharField(style={'input_type': 'password'}, write_only=True, required=False)
    confirm_password = serializers.CharField(style={'input_type': 'password'}, write_only=True, required=False)
    class Meta:
        model = User
        fields = ['first_name', 'last_name','email','old_password','new_password','confirm_password']


    def update(self, instance, validated_data):
        if 'old_password' in validated_data:
            if validated_data['new_password'] != validated_data['confirm_password']:
                raise HttpException(400, 'Las contraseñas no coinciden')

            if not instance.check_password(validated_data['old_password']):
                raise HttpException(400, 'La contraseña actual no es correcta')

            instance.set_password(validated_data['new_password'])
            instance.updated_at      = timezone.now()
            instance.user_updated_at = self.context['request'].user
            instance.save()
            return instance
        else:
            instance.updated_at      = timezone.now()
            instance.user_updated_at = self.context['request'].user
            return super().update(instance, validated_data)

class UpdatePasswordSerializer(serializers.Serializer):
    token         = serializers.CharField(write_only=True, required=True)
    uidb64        = serializers.CharField(write_only=True, required=True)
    new_password  = serializers.CharField(write_only=True, required=True)
    new_password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        fields = ['token', 'uidb64', 'new_password', 'new_password2']

    def validate(self, data):
        try:
            if data['new_password'] != data['new_password2']:
                raise HttpException(400, 'Las contraseñas no coinciden')

            id   = force_str(urlsafe_base64_decode(data['uidb64']))
            user = User.objects.get(pk=id)

           # Validar el token usando la tabla authtoken_token
            if not Token.objects.filter(user=user, key=data['token']).exists():
                raise ValidationError("El link no es válido o ha expirado.")

            user.set_password(data['new_password'])
            user.save()
            return data
        except Exception as e:
            raise HttpException(500, str(e))