from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from apps.authentication.services.session_service import is_session_revoked


def _token_was_revoked(validated_token, user):
    return (
        int(validated_token.get('token_version', 0)) != int(user.token_version)
        or is_session_revoked(validated_token.get('sid'))
    )


class RevocableJWTAuthentication(JWTAuthentication):
    def get_validated_token(self, raw_token):
        """Reject structurally incomplete access tokens before user lookup.

        SimpleJWT validates signature, expiration, issuer and audience through
        its token backend. The application-specific claims below are also
        mandatory because they bind the token to a revocable session and a
        concrete user version.
        """
        validated_token = super().get_validated_token(raw_token)
        required_claims = ("exp", "iat", "jti", "iss", "aud", "sub", "sid", "typ", "token_version")
        # ``token_version`` starts at 0 for existing users.  Zero is a valid
        # version, therefore presence must be checked explicitly instead of
        # relying on truthiness.
        if any(claim not in validated_token or validated_token.get(claim) is None for claim in required_claims):
            raise AuthenticationFailed('El token de acceso no es válido.', code='invalid_token')
        if validated_token.get('typ') != 'access':
            raise AuthenticationFailed('El token de acceso no es válido.', code='invalid_token')
        return validated_token

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        if validated_token.get('typ') != 'access' or str(validated_token.get('sub')) != str(user.pk):
            raise AuthenticationFailed('El token de acceso no es válido.', code='invalid_token')
        if _token_was_revoked(validated_token, user):
            raise AuthenticationFailed(
                'La sesión fue cerrada por un cambio de seguridad.',
                code='session_revoked',
            )
        return user
