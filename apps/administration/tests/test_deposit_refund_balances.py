from datetime import date
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.administration.api.serializers.deposit.index import DepositSerializer
from apps.administration.api.serializers.refund.index import RefundSerializer
from apps.base.exceptions import HttpException
from apps.base.utils.index import gen_uuid
from apps.client.models import Account, Client
from apps.misc.models import TypeCLient, TypeIdentity


class DepositRefundBalanceTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model(
            id=gen_uuid(), email='balance-rules@local.invalid', first_name='Balance',
            last_name='Rules', is_active=True,
        )
        self.user.set_password('SecurePass_123!')
        self.user.save()
        type_client = TypeCLient.objects.create(id=gen_uuid(), description='Juridico', user_created_at=self.user)
        type_identity = TypeIdentity.objects.create(id=gen_uuid(), description='NIT', abbreviation='NIT', user_created_at=self.user)
        self.client_record = Client.objects.create(
            id=gen_uuid(), type_client=type_client, type_identity=type_identity,
            document_number='901000001', social_reason='Saldos QA SAS',
            address='Calle 1 # 1-01', email='saldos@local.invalid', phone_number='3000000000',
            entered_by=self.user, user_created_at=self.user,
        )
        self.account = Account.objects.create(
            id=gen_uuid(), client=self.client_record, account_number='1000000001',
            balance=1000, primary=True, user_created_at=self.user,
        )
        self.request = SimpleNamespace(user=self.user)

    def test_deposit_then_refund_updates_the_account_balance(self):
        deposit = DepositSerializer(data={
            'date': str(date(2026, 1, 1)), 'client': self.client_record.id,
            'account': self.account.id, 'amount': 100, 'description': 'Depósito QA',
        }, context={'request': self.request})
        self.assertTrue(deposit.is_valid(), deposit.errors)
        deposit.save()
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, 1100)

        refund = RefundSerializer(data={
            'date': str(date(2026, 1, 2)), 'client': self.client_record.id,
            'account': self.account.id, 'amount': 30, 'gmAmount': 10,
            'applyGM': True, 'beneficiary': 'Beneficiario QA',
        }, context={'request': self.request})
        self.assertTrue(refund.is_valid(), refund.errors)
        refund.save()
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, 1060)

    def test_refund_above_available_balance_is_rejected_without_moving_money(self):
        refund = RefundSerializer(data={
            'date': str(date(2026, 1, 2)), 'client': self.client_record.id,
            'account': self.account.id, 'amount': 1001, 'gmAmount': 0,
            'applyGM': False, 'beneficiary': 'Beneficiario QA',
        }, context={'request': self.request})
        self.assertTrue(refund.is_valid(), refund.errors)

        with self.assertRaises(HttpException) as error:
            refund.save()

        self.assertEqual(error.exception.status_code, 400)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, 1000)
