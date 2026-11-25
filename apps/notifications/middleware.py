from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework.exceptions import AuthenticationFailed

from apps.authentication.jwt import RevocableJWTAuthentication


@database_sync_to_async
def get_user_from_token(raw_token):
    try:
        # WebSockets are an authenticated surface too.  Reuse the HTTP JWT
        # validator so they enforce issuer/audience, access-token type,
        # required claims, token-version and Redis session revocation.
        authentication = RevocableJWTAuthentication()
        validated_token = authentication.get_validated_token(raw_token)
        return authentication.get_user(validated_token)
    except (AuthenticationFailed, ValueError, TypeError):
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
