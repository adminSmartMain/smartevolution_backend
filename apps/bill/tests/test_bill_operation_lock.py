from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.base.utils.index import gen_uuid
from apps.bill.models import Bill
from apps.misc.models import TypeBill


class BillOperationLockTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model(
            id=gen_uuid(), email='bill-lock-admin@local.invalid', first_name='Bill',
            last_name='Lock', is_active=True, is_staff=True, is_superuser=True,
        )
        self.user.set_password('SecurePass_123!')
        self.user.save()
        self.client.force_authenticate(self.user)
        type_bill = TypeBill.objects.create(id=gen_uuid(), description='Factura', user_created_at=self.user)
        self.bill = Bill.objects.create(
            id=gen_uuid(), typeBill=type_bill, billId='QA-LOCK-1', emitterId='900000001',
            emitterName='Emisor QA', payerId='900000002', payerName='Pagador QA',
            billValue=100, subTotal=100, total=100, currentBalance=100,
            dateBill='2026-01-01', datePayment='2026-01-10', expirationDate='2026-01-10',
            user_created_at=self.user,
        )

    @patch('apps.bill.api.views.bill.index.PreOperation.objects.filter')
    def test_associated_bill_cannot_be_edited(self, operation_filter):
        operation_filter.return_value.exists.return_value = True

        response = self.client.patch(
            f'/api/bill/{self.bill.id}', {'payerName': 'Cambio no permitido'}, format='json'
        )

        self.assertEqual(response.status_code, 409)
        self.assertIn('no se puede editar', response.data['message'])
        self.bill.refresh_from_db()
        self.assertEqual(self.bill.payerName, 'Pagador QA')
