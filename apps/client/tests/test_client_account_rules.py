from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from apps.base.exceptions import HttpException
from apps.base.utils.index import gen_uuid
from apps.client.api.models.account.index import Account
from apps.client.api.models.client.index import Client
from apps.client.api.serializers.account.index import AccountSerializer
from apps.client.api.serializers.client.index import ClientSerializer
from apps.misc.models import TypeCLient, TypeIdentity


class ClientAndAccountRulesTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model(
            id=gen_uuid(),
            email='client-rules@local.invalid',
            first_name='Client',
            last_name='Rules',
            is_active=True,
        )
        self.user.set_password('SecurePass_123!')
        self.user.save()
        self.request = SimpleNamespace(user=self.user)
        self.type_client = TypeCLient.objects.create(
            id=gen_uuid(), description='Juridico', user_created_at=self.user
        )
        self.type_identity = TypeIdentity.objects.create(
            id=gen_uuid(), description='NIT', abbreviation='NIT', user_created_at=self.user
        )

    def client_data(self, document_number='900000001'):
        return {
            'type_client': self.type_client.id,
            'type_identity': self.type_identity.id,
            'document_number': document_number,
            'social_reason': 'Cliente QA SAS',
            'address': 'Calle 1 # 1-01',
            'email': 'cliente-qa@local.invalid',
            'phone_number': '3000000000',
            'entered_by': self.user.id,
        }

    def create_client(self, document_number='900000001'):
        return Client.objects.create(
            id=gen_uuid(),
            type_client=self.type_client,
            type_identity=self.type_identity,
            document_number=document_number,
            social_reason='Cliente QA SAS',
            address='Calle 1 # 1-01',
            email='cliente-qa@local.invalid',
            phone_number='3000000000',
            entered_by=self.user,
            user_created_at=self.user,
        )

    def test_client_requires_its_required_fields(self):
        serializer = ClientSerializer(data={}, context={'request': self.request})

        self.assertFalse(serializer.is_valid())
        self.assertIn('document_number', serializer.errors)
        self.assertIn('address', serializer.errors)

    def test_client_rejects_an_active_duplicate_document(self):
        self.create_client()
        serializer = ClientSerializer(data=self.client_data(), context={'request': self.request})

        self.assertFalse(serializer.is_valid())
        self.assertIn('document_number', serializer.errors)
        self.assertIn('Ya existe un cliente activo', str(serializer.errors))

    def test_client_can_reuse_document_from_an_archived_record(self):
        archived = self.create_client()
        archived.state = False
        archived.save(update_fields=['state'])
        serializer = ClientSerializer(data=self.client_data(), context={'request': self.request})

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_only_one_primary_account_can_be_created_for_a_client(self):
        client = self.create_client()
        first = AccountSerializer(
            data={'client': client.id, 'account_number': '1000000001', 'balance': 0, 'primary': True},
            context={'request': self.request},
        )
        self.assertTrue(first.is_valid(), first.errors)
        first.save()

        duplicate_primary = AccountSerializer(
            data={'client': client.id, 'account_number': '1000000002', 'balance': 0, 'primary': True},
            context={'request': self.request},
        )
        self.assertTrue(duplicate_primary.is_valid(), duplicate_primary.errors)
        with self.assertRaises(HttpException) as error:
            duplicate_primary.save()

        self.assertEqual(error.exception.status_code, 400)
        self.assertEqual(Account.objects.filter(client=client, primary=True).count(), 1)
