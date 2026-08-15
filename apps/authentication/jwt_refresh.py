from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenRefreshView

from apps.authentication.jwt import _token_was_revoked


class RevocableTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        refresh = self.token_class(attrs['refresh'])
        user_id = refresh.get('user_id')
        user = get_user_model().objects.filter(pk=user_id, is_active=True).first()
        if not user or _token_was_revoked(refresh, user):
            raise InvalidToken('La sesión ya no es válida.')
        return super().validate(attrs)


class RevocableTokenRefreshView(TokenRefreshView):
    serializer_class = RevocableTokenRefreshSerializer
