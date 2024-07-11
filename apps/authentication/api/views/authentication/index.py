# Django
from multiprocessing import context
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
# REST Framework imports
from rest_framework.decorators import APIView
# Serializers
from apps.authentication.api.serializers.index import (UserRoleSerializer, UserSerializer, UpdatePasswordSerializer)
# Models
from apps.authentication.models import User
from apps.client.models         import Client
# Utils
from apps.base.utils.index import response, sendEmail, sendWhatsApp
from apps.base.decorators.index import checkRole
# SimpleJWT
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


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
    this view is used to send a email with a reset password link
    '''
    def post(self, request):
        try:
            user          = User.objects.get(email=request.data['email'])
            uidb64        = urlsafe_base64_encode(force_bytes(user.id))
            token         = PasswordResetTokenGenerator().make_token(user)
            current_site  = get_current_site(request)
            relative_link = reverse('password-reset-confirm', kwargs={'uidb64': uidb64, 'token': token})
            url           = 'http://' + str(current_site) + str(relative_link)
            message       = 'en este link podrás restablecer tu contraseña: ' + url
            sendEmail('recuperar contraseña', message , request.data['email'],)
            return response({ 'error': False, 'message': 'email enviado'}, 200)
        except Exception as e:
            return response({ 'error': True, 'message': str(e)}, 500)


class CheckPasswordTokenAV(APIView):
    '''
    this class is used to verify if the reset password token is valid
    '''
    def get(self, request, uidb64, token):
        try:
            uid  = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=uid)
            if PasswordResetTokenGenerator().check_token(user, token):
                return response({'error': False, 'uidb64': uidb64, 'token': token}, 200)
            return response({'error': True, 'message': 'token invalido'}, 401)
        except Exception as e:
            return response({ 'error': True, 'message': str(e)}, 500)


# Reset password if the token is valid
class ResetPasswordAV(APIView):
    '''
    if the token is valid the user will update his password
    '''
    def patch(self, request):
        try:
            serializer = UpdatePasswordSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            return response({ 'error': False, 'message': 'actualización de contraseña exitosa'}, 200)
        except Exception as e:
            return response({ 'error': True, 'message': str(e)}, 500)