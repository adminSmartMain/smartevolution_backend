"""Validate configured asymmetric keys without exposing key material."""
import jwt
from django.core.exceptions import ImproperlyConfigured


def validate_jwt_key_pair(signing_key, verifying_key, algorithm):
    try:
        probe = jwt.encode({'key_check': True}, signing_key, algorithm=algorithm)
        jwt.decode(probe, verifying_key, algorithms=[algorithm])
    except Exception:
        raise ImproperlyConfigured(
            'Authentication JWT signing and verification keys are invalid or do not match.'
        ) from None
