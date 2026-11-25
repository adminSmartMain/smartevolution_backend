from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.base.utils.index import gen_uuid


class RoleAuthorizationTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model(
            id=gen_uuid(), email='no-role@local.invalid', first_name='No',
            last_name='Role', is_active=True,
        )
        self.user.set_password('SecurePass_123!')
        self.user.save()
        self.client.force_authenticate(self.user)

    def test_user_without_bill_role_receives_403_from_bill_route(self):
        response = self.client.post('/api/bill/', {'bills': []}, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['message'], 'no autorizado')
