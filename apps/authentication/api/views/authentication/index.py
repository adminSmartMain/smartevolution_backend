# Django
import logging
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from rest_framework.exceptions import APIException, AuthenticationFailed, PermissionDenied, ValidationError
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
# REST Framework imports
from rest_framework.decorators import APIView
# Serializers
from apps.authentication.api.serializers.index import (UserRoleSerializer, UserSerializer, UpdatePasswordSerializer)
# Models
from apps.authentication.models import User
from rest_framework.authtoken.models import Token
# Utils
from apps.base.utils.index import response, sendEmail, sendWhatsApp
from apps.base.decorators.index import checkRole
# SimpleJWT
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.exceptions import TokenError

from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from apps.authentication.services.login_security import (
    LoginRejected,
    SecurityStoreUnavailable,
    audit,
    check_login_attempt,
    record_failed_login,
    reset_failed_logins,
)
from apps.authentication.services.session_service import (
    issue_token_pair,
    revoke_family,
    rotate_for_user,
    validate_refresh_csrf,
)

logger = logging.getLogger(__name__)


class LoginThrottled(APIException):
    status_code = 429
    default_detail = 'No fue posible iniciar sesión. Intenta nuevamente más tarde.'
    default_code = 'login_throttled'


class AuthenticationSecurityUnavailable(APIException):
    status_code = 503
    default_detail = 'El servicio de autenticación no está disponible temporalmente.'
    default_code = 'authentication_security_unavailable'


class InvalidSession(APIException):
    """Return 401 even though refresh/logout intentionally have no bearer auth."""
    status_code = 401
    default_detail = 'La sesión no es válida.'
    default_code = 'invalid_session'


# Custom JWT Login View
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
        '''Issue a session token with no profile or authorization snapshot.

        Roles, permissions and client information are mutable authorization data.
        They belong to ``/access-control/me/`` and must not remain valid in a
        signed browser token for the life of a session.
        '''
        @classmethod
        def get_token(cls, user):
            token = super().get_token(user)
            token['sub'] = str(user.pk)
            token['typ'] = 'refresh'
            token['token_version'] = user.token_version
            return token

        def validate(self, attrs):
            email = str(attrs.get('email', '')).strip().lower()
            password = attrs.get('password', '')
            request = self.context.get('request')
            captcha_token = self.initial_data.get('captcha_token')
            try:
                check_login_attempt(request, email, captcha_token)
                # SimpleJWT delegates password verification to Django's
                # authentication backend, which intentionally runs a dummy
                # password hash when a user does not exist.
                super().validate(attrs)
            except LoginRejected as exc:
                detail = LoginThrottled.default_detail
                error = LoginThrottled(detail=detail)
                error.retry_after = exc.retry_after
                error.captcha_required = exc.captcha_required
                raise error
            except SecurityStoreUnavailable as exc:
                raise AuthenticationSecurityUnavailable() from exc
            except AuthenticationFailed:
                user = get_user_model().objects.filter(email__iexact=email, is_active=True).first()
                try:
                    captcha_required = record_failed_login(request, email, user=user)
                except LoginRejected as exc:
                    error = LoginThrottled(detail=LoginThrottled.default_detail)
                    error.retry_after = exc.retry_after
                    error.captcha_required = exc.captcha_required
                    raise error
                except SecurityStoreUnavailable as exc:
                    raise AuthenticationSecurityUnavailable() from exc
                error = AuthenticationFailed('Usuario y/o Contraseña Incorrectos')
                # The third failed attempt remains a generic 401, but tells
                # the client to obtain an invisible Turnstile token before
                # the next credential submission.
                error.captcha_required = captcha_required
                raise error

            reset_failed_logins(email)
            audit('LOGIN_SUCCEEDED', request, email, 'authenticated', user=self.user)
            try:
                return issue_token_pair(type(self), self.user)
            except SecurityStoreUnavailable as exc:
                raise AuthenticationSecurityUnavailable() from exc
            except Exception:
                raise

class LoginAV(TokenObtainPairView):
    '''
    this class is used for the login of the users using the custom token obtain pair view
    '''
    serializer_class = MyTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except LoginThrottled as exc:
            response = Response({'detail': str(exc.detail), 'captcha_required': getattr(exc, 'captcha_required', False)}, status=429)
            if getattr(exc, 'retry_after', None):
                response['Retry-After'] = str(exc.retry_after)
            return response
        except AuthenticationFailed as exc:
            return Response(
                {
                    'detail': 'Usuario y/o Contraseña Incorrectos',
                    'captcha_required': getattr(exc, 'captcha_required', False),
                },
                status=401,
            )
        payload = serializer.validated_data
        response = Response({
            'access': payload['access'],
            'token_type': 'Bearer',
            'expires_in': settings.AUTH_ACCESS_TOKEN_SECONDS,
        })
        _set_session_cookies(response, payload['refresh'], payload['csrf'])
        return response


class RefreshAV(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        refresh_value = request.COOKIES.get(settings.AUTH_REFRESH_COOKIE_NAME)
        csrf_token = request.headers.get(settings.AUTH_CSRF_HEADER_NAME)
        if not refresh_value:
            raise InvalidSession()
        try:
            # Rotate first so a replay is detected before a new access token is
            # issued. The token itself is never returned in a JSON body.
            from rest_framework_simplejwt.tokens import RefreshToken
            unverified = RefreshToken(refresh_value)
            user = get_user_model().objects.filter(pk=unverified.get('sub'), is_active=True).first()
            if not user:
                raise InvalidSession()
            payload = rotate_for_user(MyTokenObtainPairSerializer, refresh_value, csrf_token, user)
        except (ValueError, AuthenticationFailed, InvalidSession, TokenError):
            audit('REFRESH_REUSE_DETECTED', request, '', 'invalid_refresh')
            raise InvalidSession()
        except SecurityStoreUnavailable as exc:
            raise AuthenticationSecurityUnavailable() from exc
        audit('REFRESH_ROTATED', request, user.email, 'rotated', user=user)
        response = Response({'access': payload['access'], 'token_type': 'Bearer', 'expires_in': settings.AUTH_ACCESS_TOKEN_SECONDS})
        _set_session_cookies(response, payload['refresh'], payload['csrf'])
        return response


class LogoutAV(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        refresh_value = request.COOKIES.get(settings.AUTH_REFRESH_COOKIE_NAME)
        csrf_token = request.headers.get(settings.AUTH_CSRF_HEADER_NAME)
        if refresh_value:
            try:
                refresh, session_id = validate_refresh_csrf(refresh_value, csrf_token)
                revoke_family(session_id)
                audit('LOGOUT', request, request.user.email if request.user.is_authenticated else '', 'user_logout', user=request.user if request.user.is_authenticated else None)
            except ValueError as exc:
                raise PermissionDenied('Solicitud de cierre de sesión inválida.') from exc
            except Exception:
                # Logout remains idempotent and does not disclose token state.
                pass
        response = Response(status=204)
        _clear_session_cookies(response)
        return response


def _set_session_cookies(response, refresh, csrf):
    options = {
        'max_age': settings.AUTH_REFRESH_TOKEN_SECONDS,
        'secure': settings.AUTH_COOKIE_SECURE,
        'samesite': settings.AUTH_COOKIE_SAMESITE,
    }
    response.set_cookie(settings.AUTH_REFRESH_COOKIE_NAME, refresh, httponly=True, path=settings.AUTH_REFRESH_COOKIE_PATH, **options)
    response.set_cookie(settings.AUTH_CSRF_COOKIE_NAME, csrf, httponly=False, path='/', **options)


def _clear_session_cookies(response):
    response.delete_cookie(settings.AUTH_REFRESH_COOKIE_NAME, path=settings.AUTH_REFRESH_COOKIE_PATH, samesite=settings.AUTH_COOKIE_SAMESITE)
    response.delete_cookie(settings.AUTH_CSRF_COOKIE_NAME, path='/', samesite=settings.AUTH_COOKIE_SAMESITE)


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
