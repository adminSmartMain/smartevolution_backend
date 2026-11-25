"""Run only in the isolated CI Redis/MySQL environment, never against live data."""
import os

import jwt
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.base.utils.index import gen_uuid


@pytest.mark.integration
@pytest.mark.django_db
@pytest.mark.skipif(
    os.environ.get('RUN_RS256_SESSION_INTEGRATION') != '1',
    reason='Requires an isolated MySQL and Redis test environment',
)
def test_login_refresh_logout_with_rs256_and_real_redis():
    assert settings.AUTH_IS_PRODUCTION and not settings.DEBUG
    assert settings.AUTH_JWT_ALGORITHM == 'RS256'
    assert not settings.AUTH_CAPTCHA_ENABLED
    user = get_user_model()(
        id=gen_uuid(), email='rs256-integration@local.invalid',
        first_name='QA', last_name='Integration', is_active=True,
    )
    user.set_password('TestOnlyPassword_123!')
    user.save()
    client = APIClient()
    login = client.post('/api/auth/login', {
        'email': user.email, 'password': 'TestOnlyPassword_123!',
    }, format='json')
    assert login.status_code == 200
    assert 'refresh' not in login.data
    refresh_cookie = login.cookies[settings.AUTH_REFRESH_COOKIE_NAME]
    assert refresh_cookie['httponly'] and refresh_cookie['secure']
    access = login.data['access']
    claims = jwt.decode(
        access, settings.AUTH_JWT_VERIFYING_KEY, algorithms=['RS256'],
        issuer=settings.SIMPLE_JWT['ISSUER'], audience=settings.SIMPLE_JWT['AUDIENCE'],
    )
    assert claims['sub'] == str(user.pk)
    csrf = login.cookies[settings.AUTH_CSRF_COOKIE_NAME].value
    rotated = client.post('/api/auth/token/refresh', {}, format='json', HTTP_X_CSRF_TOKEN=csrf)
    assert rotated.status_code == 200
    assert rotated.cookies[settings.AUTH_REFRESH_COOKIE_NAME].value != refresh_cookie.value
    new_csrf = rotated.cookies[settings.AUTH_CSRF_COOKIE_NAME].value
    logout = client.post('/api/auth/logout', {}, format='json', HTTP_X_CSRF_TOKEN=new_csrf)
    assert logout.status_code == 204
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {rotated.data['access']}")
    assert client.get('/api/access-control/me/').status_code == 401
