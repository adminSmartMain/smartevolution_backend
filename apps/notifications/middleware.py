from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

from apps.authentication.models import User


@database_sync_to_async
def get_user_from_token(raw_token):
    try:
        validated_token = AccessToken(raw_token)

        user_id = validated_token.get("user_id")

        if not user_id:
            return AnonymousUser()

        user = User.objects.filter(
            pk=user_id,
            is_active=True,
        ).first()

        if not user:
            return AnonymousUser()

        token_version = int(
            validated_token.get("token_version", 0)
        )

        if token_version != int(user.token_version):
            return AnonymousUser()

        return user

    except (InvalidToken, TokenError, ValueError, TypeError):
        return AnonymousUser()


class JWTAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        query_string = scope.get(
            "query_string",
            b"",
        ).decode()

        params = parse_qs(query_string)

        token = params.get("token", [None])[0]

        if token:
            scope["user"] = await get_user_from_token(token)
        else:
            scope["user"] = AnonymousUser()

        return await self.app(
            scope,
            receive,
            send,
        )