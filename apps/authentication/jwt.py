from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed


def _token_was_revoked(validated_token, user):
    return int(validated_token.get('token_version', 0)) != int(user.token_version)


class RevocableJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        if _token_was_revoked(validated_token, user):
            raise AuthenticationFailed(
                'La sesión fue cerrada por un cambio de seguridad.',
                code='session_revoked',
            )
        return user
