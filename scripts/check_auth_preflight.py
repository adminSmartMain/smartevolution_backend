"""Fail closed without printing credentials during deployment preflight."""
import redis
from django.conf import settings


def check():
    if settings.DEBUG or not settings.AUTH_IS_PRODUCTION or settings.AUTH_JWT_ALGORITHM != 'RS256':
        raise SystemExit('Deployment requires DEBUG=False and strict RS256 authentication.')
    try:
        redis.Redis.from_url(settings.AUTH_REDIS_URL, socket_connect_timeout=5, socket_timeout=5).ping()
    except (redis.RedisError, ValueError):
        raise SystemExit('Authentication Redis is unavailable; deployment stopped.') from None
    print('Authentication policy and Redis preflight passed.')
