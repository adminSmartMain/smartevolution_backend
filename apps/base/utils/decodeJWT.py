import jwt
from django.conf import settings


def decodeJWT(token):
    try:
        return jwt.decode(token.META.get('HTTP_AUTHORIZATION').split(' ')[1], settings.SECRET_KEY, algorithms=['HS256'])
    except Exception as e:
        return {'error': str(e)}


def decodePermissionToken(token):
    return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
