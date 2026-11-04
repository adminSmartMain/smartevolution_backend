from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from apps.base.utils.index import gen_uuid


class LoginSessionSecurityTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model(
            id=gen_uuid(), email='login-security@local.invalid', first_name='Login',
            last_name='Security', is_active=True,
        )
        self.user.set_password('SecurePass_123!')
        self.user.save()

    def test_valid_credentials_issue_access_and_refresh_tokens(self):
        response = self.client.post('/api/auth/login', {
            'email': self.user.email,
            'password': 'SecurePass_123!',
        }, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_invalid_credentials_do_not_issue_tokens(self):
        response = self.client.post('/api/auth/login', {
            'email': self.user.email,
            'password': 'WrongPass_123!',
        }, format='json')

        self.assertEqual(response.status_code, 401)
        self.assertNotIn('access', response.data)

    def test_expired_access_token_is_rejected_by_protected_endpoint(self):
        token = AccessToken.for_user(self.user)
        token['token_version'] = self.user.token_version
        token['exp'] = int((timezone.now() - timedelta(minutes=1)).timestamp())
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        response = self.client.get('/api/access-control/me/')

        self.assertEqual(response.status_code, 401)
