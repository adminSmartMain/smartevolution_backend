import json
import logging
import secrets

import redis
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.services.login_security import SecurityStoreUnavailable, _redis

logger = logging.getLogger(__name__)


def issue_token_pair(serializer_class, user):
    refresh = serializer_class.get_token(user)
    session_id = secrets.token_urlsafe(24)
    csrf_token = secrets.token_urlsafe(32)
    refresh["sid"] = session_id
    refresh["token_version"] = user.token_version
    client = _redis()
    client.setex(
        f"auth:session:{session_id}", settings.AUTH_REFRESH_TOKEN_SECONDS,
        json.dumps({"user_id": str(user.id), "csrf": csrf_token}),
    )
    client.setex(f"auth:refresh:{refresh['jti']}", settings.AUTH_REFRESH_TOKEN_SECONDS, session_id)
    access = refresh.access_token
    access["typ"] = "access"
    return {"access": str(access), "refresh": str(refresh), "csrf": csrf_token}


def rotate_refresh(refresh_value, csrf_token):
    refresh = RefreshToken(refresh_value)
    session_id = refresh.get("sid")
    jti = refresh.get("jti")
    if not session_id or not jti:
        raise ValueError("Invalid refresh token")
    client = _redis()
    raw_session = client.get(f"auth:session:{session_id}")
    if not raw_session:
        revoke_family(session_id)
        raise ValueError("Refresh token reuse detected")
    session = json.loads(raw_session)
    if not csrf_token or not secrets.compare_digest(session.get("csrf", ""), csrf_token):
        raise ValueError("CSRF validation failed")
    expected_session = client.getdel(f"auth:refresh:{jti}")
    if expected_session != session_id:
        revoke_family(session_id)
        raise ValueError("Refresh token reuse detected")
    return refresh, session, client


def rotate_for_user(serializer_class, refresh_value, csrf_token, user):
    old_refresh, session, client = rotate_refresh(refresh_value, csrf_token)
    new_refresh = serializer_class.get_token(user)
    new_refresh["sid"] = old_refresh["sid"]
    new_refresh["token_version"] = user.token_version
    client.setex(f"auth:refresh:{new_refresh['jti']}", settings.AUTH_REFRESH_TOKEN_SECONDS, old_refresh["sid"])
    access = new_refresh.access_token
    access["typ"] = "access"
    return {"access": str(access), "refresh": str(new_refresh), "csrf": session["csrf"], "sid": old_refresh["sid"]}


def revoke_family(session_id):
    if not session_id:
        return
    client = _redis()
    client.delete(f"auth:session:{session_id}")
    client.setex(f"auth:revoked-session:{session_id}", settings.AUTH_REFRESH_TOKEN_SECONDS, "1")


def validate_refresh_csrf(refresh_value, csrf_token):
    refresh = RefreshToken(refresh_value)
    session_id = refresh.get("sid")
    if not session_id or not csrf_token:
        raise ValueError("CSRF validation failed")
    raw_session = _redis().get(f"auth:session:{session_id}")
    if not raw_session:
        raise ValueError("Invalid refresh token")
    session = json.loads(raw_session)
    if not secrets.compare_digest(session.get("csrf", ""), csrf_token):
        raise ValueError("CSRF validation failed")
    return refresh, session_id


def is_session_revoked(session_id):
    if not session_id:
        return False
    try:
        return bool(_redis().exists(f"auth:revoked-session:{session_id}"))
    except SecurityStoreUnavailable:
        return True
