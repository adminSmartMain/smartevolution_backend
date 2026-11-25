import jwt
from django.conf import settings
from rest_framework_simplejwt.settings import api_settings


def _jwt_options(expected_type=None):
    options = {"require": ["exp", "iat", "jti", "sub", "typ"]}
    if expected_type:
        options["verify_signature"] = True
    return options


def _decode(raw_token, expected_type="access"):
    algorithm = settings.SIMPLE_JWT["ALGORITHM"]
    verification_key = (
        api_settings.VERIFYING_KEY
        if algorithm.startswith(("RS", "ES", "PS"))
        else api_settings.SIGNING_KEY
    )
    payload = jwt.decode(
        raw_token,
        verification_key,
        algorithms=[algorithm],
        issuer=settings.SIMPLE_JWT["ISSUER"],
        audience=settings.SIMPLE_JWT["AUDIENCE"],
        options=_jwt_options(expected_type),
    )
    if payload.get("typ") != expected_type:
        raise jwt.InvalidTokenError("Unexpected token type")
    return payload


def decodeJWT(request):
    try:
        authorization = request.META.get("HTTP_AUTHORIZATION", "")
        scheme, raw_token = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            raise jwt.InvalidTokenError("Unexpected authorization scheme")
        return _decode(raw_token)
    except Exception:
        # Callers must not receive crypto/parser detail in an HTTP response.
        return {"error": "Invalid token"}


def decodePermissionToken(token):
    return _decode(token)
