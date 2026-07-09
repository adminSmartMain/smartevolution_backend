import re

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.base.utils.index import gen_uuid


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='test@local.invalid',
    FRONTEND_URL='http://localhost:3000',
)
class PasswordResetFlowTests(APITestCase):
    def setUp(self):
        self.user = get_user_model()(id=gen_uuid(), email='password-flow-test@local.invalid', first_name='Password', last_name='Test', is_active=True)
        self.user.set_password('OldPass_123!')
        self.user.save()

    def test_complete_password_reset_flow(self):
        requested = self.client.post('/api/auth/reset-password', {'email': self.user.email}, format='json')
        self.assertEqual(requested.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

        match = re.search(r'uidb64=([^&]+)(?:&amp;|&)token=([^"<]+)', mail.outbox[0].body)
        self.assertIsNotNone(match)
        uidb64, token = match.groups()

        verified = self.client.get(f'/api/auth/token/verify/{uidb64}/{token}/')
        self.assertEqual(verified.status_code, 200)

        changed = self.client.patch('/api/auth/reset-password-complete', {
            'uidb64': uidb64,
            'token': token,
            'new_password': 'NewSecure_456.',
            'new_password2': 'NewSecure_456.',
        }, format='json')
        self.assertEqual(changed.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewSecure_456.'))

        reused = self.client.get(f'/api/auth/token/verify/{uidb64}/{token}/')
        self.assertEqual(reused.status_code, 400)

    def test_unknown_email_does_not_disclose_account(self):
        response = self.client.post('/api/auth/reset-password', {'email': 'unknown@local.invalid'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)
