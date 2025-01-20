# Django
from multiprocessing import context
from django.contrib.auth.tokens import PasswordResetTokenGenerator
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

                # Get User Roles
                roles.append('superuser') if is_superuser else None
                userRoles = UserRoleSerializer.Meta.model.objects.filter(user=user)
                for role in userRoles:
                    roles.append(role.role.description)
                # get client information
                client = Client.objects.filter(user=user).first()
                # Set JWT Payload
                token['name']         = f'{user.first_name} {user.last_name}'
                token['roles']        = roles
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
            # Validar que el email esté presente en el request
            if 'email' not in request.data or not request.data['email']:
                raise ValidationError("El campo 'email' es obligatorio.")

            # Buscar el usuario por correo
            user = User.objects.get(email=request.data['email'])
            
            
             # Eliminar cualquier token anterior asociado al usuario
            Token.objects.filter(user=user).delete()

            # Generar un nuevo token
            token_obj = Token.objects.create(user=user)
            token_obj.created = timezone.now()  # Actualizar la fecha de creación
            token_obj.save()
            
           
            # Generar URL de restablecimiento
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = f'https://devapp.smartevolution.com.co/auth/resetPassword?uidb64={uidb64}&token={token_obj.key}'

            
            # Renderizar el mensaje HTML
            html_message = render_to_string('reset_password_email.html', {
                'user': user,
                'reset_url': reset_url,
            })
            
            # Enviar el correo
            sendEmail(
                subject='Recuperar Contraseña',
                message='Este es un correo de recuperación de contraseña.',
                email=request.data['email'],
                html_message=html_message
            )
            
            # Respuesta exitosa
            return Response({'error': False, 'message': 'Correo enviado correctamente'}, status=200)
        
        except ObjectDoesNotExist:
            # Manejar el caso de que el correo no esté en la base de datos
            return Response({'error': True, 'message': 'El correo no se encuentra registrado'}, status=404)
        
        except ValidationError as ve:
            # Manejar validaciones específicas
            return Response({'error': True, 'message': str(ve)}, status=400)
        
        except Exception as e:
            # Manejar errores no previstos
            return Response({'error': True, 'message': 'Error interno del servidor'}, status=500)


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

            
            # Verificar si el token existe en la base de datos
            try:
                token_obj = Token.objects.get(key=token, user=user)
            except Token.DoesNotExist:
                return Response({'error': True, 'message': 'Token inválido o no encontrado'}, status=404)

           # Verificar si el token ha expirado (1 hora)
            expiration_time = token_obj.created + timezone.timedelta(hours=1)
            if timezone.now() > expiration_time:
                token_obj.delete()  # Invalidar el token expirado
                return Response({'error': True, 'message': 'Token expirado'}, status=401)

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
              # Buscar el usuario por correo
            logger.debug(f"request.data: {request.data}")
            token=Token.objects.filter(key=request.data['token']).first() 
            logger.debug(token.user_id)
            user_token=User.objects.filter(id=token.user_id).first() 
            logger.debug(f"Atributos completos del usuario: {vars(user_token)}")
            
            html_message = render_to_string('succesful_reset_password.html', {
                'user': user_token,
               
            })
            
            # Enviar el correo
            sendEmail(
                subject='Recuperación de contraseña exitosa',
                message='Esto es un correo de confirmación de recuperacion de contraseña',
                email= user_token.email,
                html_message=html_message
            )
             # Eliminar cualquier token anterior asociado al usuario
            Token.objects.filter(key=request.data['token']).delete()
             # Renderizar el mensaje HTML
               # Buscar el usuario por correo
          
            
            return response({ 'error': False, 'message': 'actualización de contraseña exitosa'}, 200)
        except Exception as e:
            return response({ 'error': True, 'message': str(e)}, 500)