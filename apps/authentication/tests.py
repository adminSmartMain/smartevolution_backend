from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.authentication.api.models.role.index import Role
from apps.authentication.api.models.user.index import User
from apps.authentication.api.models.userRole.index import UserRole
from apps.authentication.jwt import RevocableJWTAuthentication
from apps.base.utils.index import gen_uuid


class UserAdministrationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create(
            id=gen_uuid(),
            email='admin-users@example.com',
            first_name='Admin',
            last_name='Users',
            is_active=True,
            is_superuser=True,
        )
        self.admin.set_password('AdminPass123!')
        self.admin.save(update_fields=['password'])
        self.role = Role.objects.create(
            id=gen_uuid(),
            code='TEST_ROLE',
            name='Rol de prueba',
            description='Rol para pruebas de administración',
            audience='INTERNAL',
            state=True,
        )
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def create_target(self, email='target@example.com'):
        user = User.objects.create(
            id=gen_uuid(),
            email=email,
            first_name='Target',
            last_name='User',
            is_active=True,
        )
        user.set_password('TargetPass123!')
        user.save(update_fields=['password'])
        UserRole.objects.create(id=gen_uuid(), user=user, role=self.role)
        return user

    def test_create_and_get_complete_user_profile(self):
        response = self.client.post('/api/access-control/users/', {
            'email': 'new.user@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'phone_number': '+57 300 000 0000',
            'organization': 'Smart Evolution',
            'description': 'Nota administrativa',
            'roles': ['TEST_ROLE'],
        }, format='json')
        self.assertEqual(response.status_code, 201)
        user_id = response.data['data']['id']
        detail = self.client.get(f'/api/access-control/users/{user_id}/')
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data['data']['organization'], 'Smart Evolution')
        self.assertEqual(detail.data['data']['description'], 'Nota administrativa')
        self.assertEqual(detail.data['data']['roles'], ['TEST_ROLE'])

    def test_edit_rejects_duplicate_email(self):
        target = self.create_target()
        other = self.create_target('other@example.com')
        response = self.client.patch(
            f'/api/access-control/users/{target.id}/',
            {'email': other.email},
            format='json',
        )
        self.assertEqual(response.status_code, 400)

    def test_password_change_hashes_password_and_revokes_old_tokens(self):
        target = self.create_target()
        old_token = AccessToken.for_user(target)
        old_token['token_version'] = target.token_version
        response = self.client.post(
            f'/api/access-control/users/{target.id}/password/',
            {'new_password': 'UpdatedPass123!', 'confirm_password': 'UpdatedPass123!'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        target.refresh_from_db()
        self.assertTrue(target.check_password('UpdatedPass123!'))
        with self.assertRaises(Exception):
            RevocableJWTAuthentication().get_user(old_token)

    def test_archive_and_restore_are_reversible(self):
        target = self.create_target()
        archived = self.client.post(f'/api/access-control/users/{target.id}/archive/', {}, format='json')
        self.assertEqual(archived.status_code, 200)
        target.refresh_from_db()
        self.assertFalse(target.is_active)
        self.assertIsNotNone(target.archived_at)
        restored = self.client.post(f'/api/access-control/users/{target.id}/restore/', {}, format='json')
        self.assertEqual(restored.status_code, 200)
        target.refresh_from_db()
        self.assertTrue(target.is_active)
        self.assertIsNone(target.archived_at)

    def test_user_metrics_are_aggregated_by_the_backend(self):
        self.create_target()
        blocked = self.create_target('blocked@example.com')
        blocked.is_active = False
        blocked.save(update_fields=['is_active'])

        response = self.client.get('/api/access-control/users/metrics/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['total_users'], 3)
        self.assertEqual(response.data['data']['active_users'], 2)
        self.assertEqual(response.data['data']['blocked_users'], 1)
        self.assertEqual(response.data['data']['active_percentage'], 66.7)
