# Django
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.password_validation import validate_password
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.template.loader import render_to_string
from django.db import transaction
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

import logging

# Configurar el logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Crear un handler de consola y definir el nivel
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Crear un formato para los mensajes de log
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Añadir el handler al logger
logger.addHandler(console_handler)


class UserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(style={'input_type': 'text'}, write_only=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name','email','role', 'description', 'phone_number', 'profile_photo']
        extra_kwargs = {
            'email'     : {'required': True},
            'first_name': {'required': True},
            'last_name' : {'required': True},
            'role'      : {'required': True},
        }

    def save(self):
        email = self.validated_data['email'].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise HttpException(400, 'El correo ya se encuentra registrado')

        temporary_password = generatePassword(12)
        code = generatePassword(12)
        while User.objects.filter(code=code).exists():
            code = generatePassword(12)

        description = self.validated_data.get('description', '')
        role_id = self.validated_data['role']

        # User + role are one database operation. SMTP delivery is deliberately
        # outside the transaction: an email outage must not delete a valid user.
        try:
            with transaction.atomic():
                account = User(
                    id=gen_uuid(),
                    email=email,
                    first_name=self.validated_data['first_name'],
                    last_name=self.validated_data['last_name'],
                    description=description,
                    phone_number=self.validated_data.get('phone_number'),
                    profile_photo=self.validated_data.get('profile_photo'),
                    code=code,
                    is_active=True,
                )
                account.set_password(temporary_password)
                account.save()

                UserRole.objects.create(
                    id=gen_uuid(),
                    user_id=account.id,
                    role_id=role_id,
                )
        except Exception as exc:
            if isinstance(exc, HttpException):
                raise
            raise HttpException(500, str(exc))

        # Every user created from Administration receives credentials. Do not
        # couple persistence to SMTP: the account remains valid if delivery fails.
        try:
            html_message = render_to_string('success_register.html', {
                'user': account,
                'password': temporary_password,
            })
            delivered = sendEmail(
                subject='Credencial de acceso',
                message=(
                    f'Hola {account.first_name or account.description}, '
                    'te damos la bienvenida a Smart Evolution.'
                ),
                email=account.email,
                html_message=html_message,
            )
            if delivered != 1:
                logger.warning(
                    'SMTP no confirmó el correo de bienvenida para el usuario %s',
                    account.pk,
                )
        except Exception:
            logger.exception(
                'Usuario %s creado correctamente, pero falló el correo de bienvenida.',
                account.pk,
            )

        return account


class UserReadOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['id', 'first_name', 'last_name', 'email', 'profile_photo']
        read_only_fields = ['id', 'first_name', 'last_name', 'email', 'profile_photo']

class UpdateUserSerializer(serializers.ModelSerializer):
    old_password     = serializers.CharField(style={'input_type': 'password'}, write_only=True, required=False)
    new_password     = serializers.CharField(style={'input_type': 'password'}, write_only=True, required=False)
    confirm_password = serializers.CharField(style={'input_type': 'password'}, write_only=True, required=False)
    class Meta:
        model = User
        fields = ['first_name', 'last_name','email','profile_photo','old_password','new_password','confirm_password']


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
        if data['new_password'] != data['new_password2']:
            raise serializers.ValidationError({'new_password2': 'Las contraseñas no coinciden.'})
        try:
            user_id = force_str(urlsafe_base64_decode(data['uidb64']))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({'token': 'El enlace no es válido o ha expirado.'})
        if not default_token_generator.check_token(user, data['token']):
            raise serializers.ValidationError({'token': 'El enlace no es válido o ha expirado.'})
        validate_password(data['new_password'], user=user)
        data['user'] = user
        return data

    def create(self, validated_data):
        user = validated_data['user']
        user.set_password(validated_data['new_password'])
        user.save(update_fields=['password'])
        return user
