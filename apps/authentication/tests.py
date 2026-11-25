from django.test import TestCase
from django.test import SimpleTestCase, override_settings
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch
from rest_framework.test import APIClient
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from apps.authentication.api.models.role.index import Role
from apps.authentication.api.models.user.index import User
from apps.authentication.api.models.userRole.index import UserRole
from apps.authentication.jwt import RevocableJWTAuthentication
from apps.base.utils.index import gen_uuid
from apps.authentication.services.login_security import LoginRejected, _identifier


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


class AuthFakeRedis:
    def __init__(self):
        self.values = {}
        self.ttls = {}
        self.sets = {}

    def ping(self): return True
    def get(self, key): return self.values.get(key)
    def setex(self, key, ttl, value): self.values[key], self.ttls[key] = value, ttl
    def getdel(self, key): return self.values.pop(key, None)
    def delete(self, *keys):
        for key in keys:
            self.values.pop(key, None)
            self.ttls.pop(key, None)
    def exists(self, key): return int(key in self.values)
    def incr(self, key):
        self.values[key] = int(self.values.get(key, 0)) + 1
        return self.values[key]
    def sadd(self, key, *values):
        self.sets.setdefault(key, set()).update(values)
        return len(values)
    def scard(self, key): return len(self.sets.get(key, set()))
    def expire(self, key, ttl): self.ttls[key] = ttl
    def ttl(self, key): return self.ttls.get(key, -1)


class LoginSecurityServiceTests(SimpleTestCase):
    @override_settings(AUTH_CAPTCHA_ENABLED=False, AUTH_CAPTCHA_AFTER_FAILURES=3)
    @patch('apps.authentication.services.login_security.time.sleep')
    @patch('apps.authentication.services.login_security.audit')
    @patch('apps.authentication.services.login_security._redis')
    def test_disabled_captcha_never_requested_but_backoff_and_lock_remain(self, redis_factory, audit, sleep):
        from apps.authentication.services.login_security import check_login_attempt, record_failed_login
        store = AuthFakeRedis()
        redis_factory.return_value = store
        request = type('Request', (), {'META': {}})()
        for _ in range(3):
            self.assertFalse(record_failed_login(request, 'user@example.com'))
        with self.assertRaises(LoginRejected) as fourth:
            record_failed_login(request, 'user@example.com')
        self.assertFalse(fourth.exception.captcha_required)
        with self.assertRaises(LoginRejected) as backoff:
            check_login_attempt(request, 'user@example.com', None)
        self.assertFalse(backoff.exception.captcha_required)
        with self.assertRaises(LoginRejected) as fifth:
            record_failed_login(request, 'user@example.com')
        self.assertEqual(fifth.exception.retry_after, 15 * 60)

    def test_identifier_is_case_insensitive_and_not_raw_email(self):
        value = _identifier('User@Example.com')
        self.assertEqual(value, _identifier(' user@example.com '))
        self.assertNotIn('user@example.com', value)

    @patch('apps.authentication.services.login_security._redis')
    @patch('apps.authentication.services.login_security.audit')
    def test_fifth_failure_locks_the_account(self, audit, redis_factory):
        from apps.authentication.services.login_security import record_failed_login
        store = AuthFakeRedis()
        redis_factory.return_value = store
        request = type('Request', (), {'META': {}})()
        for _ in range(4):
            try:
                record_failed_login(request, 'user@example.com')
            except LoginRejected:
                pass
        with self.assertRaises(LoginRejected) as raised:
            record_failed_login(request, 'user@example.com')
        self.assertEqual(raised.exception.retry_after, 15 * 60)


class LoginSessionSecurityTests(APITestCase):
    def setUp(self):
        self.redis = AuthFakeRedis()
        self.login_redis = patch('apps.authentication.services.login_security._redis', return_value=self.redis)
        self.session_redis = patch('apps.authentication.services.session_service._redis', return_value=self.redis)
        self.login_redis.start()
        self.session_redis.start()
        self.addCleanup(self.login_redis.stop)
        self.addCleanup(self.session_redis.stop)
        self.user = User(id=gen_uuid(), email='login-security@local.invalid', first_name='Login', last_name='Security', is_active=True)
        self.user.set_password('SecurePass_123!')
        self.user.save()

    def login(self):
        return self.client.post('/api/auth/login', {'email': self.user.email, 'password': 'SecurePass_123!'}, format='json')

    def test_login_issues_memory_access_and_http_only_refresh_cookie(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertNotIn('refresh', response.data)
        self.assertTrue(response.cookies['se_refresh']['httponly'])

    def test_invalid_credentials_do_not_issue_tokens(self):
        response = self.client.post('/api/auth/login', {
            'email': self.user.email, 'password': 'WrongPass_123!',
        }, format='json')
        self.assertEqual(response.status_code, 401)
        self.assertNotIn('access', response.data)
        self.assertNotIn('se_refresh', response.cookies)

    def test_local_frontend_is_allowed_to_establish_cookie_session(self):
        response = self.client.options('/api/auth/login', HTTP_ORIGIN='http://localhost:3000', HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Access-Control-Allow-Origin'], 'http://localhost:3000')
        self.assertEqual(response['Access-Control-Allow-Credentials'], 'true')

    def test_access_payload_does_not_expose_profile_or_permissions(self):
        response = self.login()
        token = AccessToken(response.data['access'])
        self.assertEqual(token['sub'], str(self.user.pk))
        self.assertEqual(token['typ'], 'access')
        for claim in ('name', 'roles', 'permissions', 'client', 'profile_photo'):
            self.assertNotIn(claim, token)

    def test_reusing_rotated_refresh_revokes_the_session_family(self):
        login = self.login()
        old_refresh, csrf, old_access = login.cookies['se_refresh'].value, login.cookies['se_csrf'].value, login.data['access']
        first_refresh = self.client.post('/api/auth/token/refresh', {}, format='json', HTTP_X_CSRF_TOKEN=csrf)
        self.assertEqual(first_refresh.status_code, 200)
        self.client.cookies['se_refresh'] = old_refresh
        replay = self.client.post('/api/auth/token/refresh', {}, format='json', HTTP_X_CSRF_TOKEN=csrf)
        self.assertEqual(replay.status_code, 401)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {old_access}')
        self.assertEqual(self.client.get('/api/access-control/me/').status_code, 401)

    def test_logout_revokes_access_token_from_current_session(self):
        login = self.login()
        self.assertEqual(self.client.post('/api/auth/logout', {}, format='json', HTTP_X_CSRF_TOKEN=login.cookies['se_csrf'].value).status_code, 204)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {login.data["access"]}')
        self.assertEqual(self.client.get('/api/access-control/me/').status_code, 401)

    def test_expired_access_token_is_rejected(self):
        token = AccessToken.for_user(self.user)
        token['token_version'], token['sub'], token['typ'] = self.user.token_version, str(self.user.pk), 'access'
        token['exp'] = int((timezone.now() - timedelta(minutes=1)).timestamp())
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(self.client.get('/api/access-control/me/').status_code, 401)
