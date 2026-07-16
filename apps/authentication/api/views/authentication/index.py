# Django
from multiprocessing import context
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
# REST Framework imports
from rest_framework.decorators import APIView
# Serializers
from apps.authentication.api.serializers.index import (UserRoleSerializer, UserSerializer, UpdatePasswordSerializer)
# Models
from apps.authentication.models import User
from apps.client.models         import Client
from rest_framework.authtoken.models import Token
# Utils
from apps.base.utils.index import response, sendEmail, sendWhatsApp
from apps.base.decorators.index import checkRole
# SimpleJWT
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from apps.authentication.access import get_access_profile
from django.conf import settings


# Custom JWT Login View
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
        '''
        in this class we are overriding the default method of the TokenObtainPairSerializer class
        for generating the token, we are adding the user roles and the user information to the payload
        '''
        def get_token(self, user):
            try:
                roles        = []
                token        = super().get_token(user)
                is_superuser = user.is_superuser

                profile = get_access_profile(user)
                roles = profile['roles']
                roles.append('superuser') if is_superuser else None
                client = Client.objects.filter(pk=profile['client']).first() if profile['client'] else Client.objects.filter(user=user).first()
                # Set JWT Payload
                token['name']         = f'{user.first_name} {user.last_name}'
                token['roles']        = roles
                token['permissions']  = profile['permissions']
                token['account_scope'] = profile['account_scope']
                token['client_access_status'] = profile['client_access_status']
                token['client_portal_enabled'] = profile['client_portal_enabled']
                token['profile_photo'] = profile.get('profile_photo')
                token['is_superuser'] = is_superuser
                if is_superuser == False and client:
                    # get client information
                    token['client']       = client.id
                    token['client_name']  = client.first_name + ' ' + client.last_name if client.first_name and client.last_name else client.social_reason

                    if client.status == 0:
                        return response({'error': True, 'message': 'cliente no validado'}, 401)
                    elif client.status == 2:
                        return response({'error': True, 'message': 'cliente no autorizado'}, 401)

                return token

            except Exception as e:
                return response({'error': True, 'message':str(e)}, 500)

class LoginAV(TokenObtainPairView):
    '''
    this class is used for the login of the users using the custom token obtain pair view
    '''
    serializer_class = MyTokenObtainPairSerializer


class RegisterAV(APIView):
    '''
    this class is used for the registration of the users
    '''

    @checkRole(['superuser'])
    def post(self, request):
        try:
            serializer = UserSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'message': 'registro exitoso'}, 201)
            return response({'error': True, 'message': serializer.errors}, 400)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)


class ForgotPasswordAV(APIView):
    '''
    This view is used to send an email with a reset password link.
    '''
    def post(self, request):
        try:
            email = str(request.data.get('email', '')).strip().lower()
            if not email:
                raise ValidationError("El campo 'email' es obligatorio.")
            user = User.objects.filter(email__iexact=email, is_active=True).first()
            if not user:
                return Response({'error': False, 'message': 'Si el correo está registrado, recibirás un enlace de recuperación.'}, status=200)
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = f'{settings.FRONTEND_URL}/auth/resetPassword?uidb64={uidb64}&token={token}'
            html_message = render_to_string('reset_password_email.html', {
                'user': user,
                'reset_url': reset_url,
            })
            sent = sendEmail(
                subject='Recuperar Contraseña',
                message='Este es un correo de recuperación de contraseña.',
                email=user.email,
                html_message=html_message
            )
            if sent != 1:
                raise RuntimeError('El servidor SMTP no confirmó el envío.')
            return Response({'error': False, 'message': 'Si el correo está registrado, recibirás un enlace de recuperación.'}, status=200)
        except ValidationError as ve:
            return Response({'error': True, 'message': str(ve)}, status=400)
        except Exception as e:
            logger.exception('No fue posible enviar el correo de recuperación: %s', e)
            return Response({'error': True, 'message': 'No fue posible enviar el correo. Intenta nuevamente o contacta al administrador.'}, status=503)


class CheckPasswordTokenAV(APIView):
    '''
    This class is used to verify if the reset password token is valid.
    '''

    def get(self, request, uidb64, token):
        try:
            # Decodificar el UID del usuario
            try:
                uid = force_str(urlsafe_base64_decode(uidb64))
                user = User.objects.get(id=uid)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                return Response({'error': True, 'message': 'UID inválido o usuario no encontrado'}, status=404)

            
            if not default_token_generator.check_token(user, token):
                return Response({'error': True, 'message': 'El enlace no es válido o ha expirado.'}, status=400)
            return Response({'error': False, 'message': 'Token válido'}, status=200)

        except Exception as e:
            return Response({'error': True, 'message': 'Error interno del servidor'}, status=500)



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
# Reset password if the token is valid
class ResetPasswordAV(APIView):
    '''
    if the token is valid the user will update his password
    '''
    def patch(self, request):
        try:
            serializer = UpdatePasswordSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            html_message = render_to_string('succesful_reset_password.html', {
                'user': user,
            })
            try:
                sendEmail(subject='Contraseña actualizada', message='Tu contraseña fue actualizada correctamente.', email=user.email, html_message=html_message)
            except Exception:
                logger.exception('La contraseña cambió, pero falló el correo de confirmación para el usuario %s', user.pk)
            return response({'error': False, 'message': 'Contraseña actualizada correctamente.'}, 200)
        except ValidationError as e:
            return response({'error': True, 'message': e.detail}, 400)
        except Exception as e:
            logger.exception('Error al actualizar contraseña: %s', e)
            return response({'error': True, 'message': 'No fue posible actualizar la contraseña.'}, 500)
