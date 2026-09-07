from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import requests
from django.test import SimpleTestCase

from apps.bill.services.billy.client import BillyClient
from apps.bill.services.billy.exceptions import (
    BillyAPIError,
    BillyLocalRateLimitError,
    BillyNotFoundError,
    BillyRateLimitError,
    BillyTimeoutError,
)
from apps.bill.services.billy.polling import calculate_next_check
from apps.bill.services.billy.upload_service import BillyUploadService
from apps.bill.tasks import _get_retry_countdown
from apps.bill.utils.updateMassiveTypeBill import (
    UUID_ENDOSADA,
    UUID_FV,
    UUID_PAGADA,
    UUID_RECHAZADA,
)


class FakeRateLimiter:
    def __init__(
        self,
        allowed=True,
        retry_after=0,
        count=1,
        limit=400,
    ):
        self.allowed = allowed
        self.retry_after = retry_after
        self.count = count
        self.limit = limit

    def acquire(self):
        return {
            "allowed": self.allowed,
            "retry_after": self.retry_after,
            "count": self.count,
            "limit": self.limit,
        }


class FakeResponse:
    def __init__(
        self,
        status_code=200,
        payload=None,
        headers=None,
        text="",
    ):
        self.status_code = status_code
        self._payload = payload
        self.headers = headers or {}
        self.text = text

    def json(self):
        if isinstance(
            self._payload,
            Exception,
        ):
            raise self._payload

        return self._payload or {}


class BillyPollingTests(SimpleTestCase):
    def setUp(self):
        self.now = datetime(
            2026,
            9,
            2,
            10,
            0,
            0,
        )

    def test_fv_se_revisa_en_una_hora(self):
        result = calculate_next_check(
            UUID_FV,
            self.now,
        )

        self.assertEqual(
            result,
            self.now + timedelta(hours=1),
        )

    def test_endosada_se_revisa_en_24_horas(self):
        result = calculate_next_check(
            UUID_ENDOSADA,
            self.now,
        )

        self.assertEqual(
            result,
            self.now + timedelta(hours=24),
        )

    def test_pagada_desactiva_polling(self):
        result = calculate_next_check(
            UUID_PAGADA,
            self.now,
        )

        self.assertIsNone(result)

    def test_rechazada_desactiva_polling(self):
        result = calculate_next_check(
            UUID_RECHAZADA,
            self.now,
        )

        self.assertIsNone(result)


class BillyRetryTests(SimpleTestCase):
    def test_backoff_tecnico(self):
        self.assertEqual(
            _get_retry_countdown(0),
            15 * 60,
        )

        self.assertEqual(
            _get_retry_countdown(1),
            30 * 60,
        )

        self.assertEqual(
            _get_retry_countdown(2),
            60 * 60,
        )

        self.assertEqual(
            _get_retry_countdown(3),
            2 * 60 * 60,
        )

    def test_backoff_no_supera_ultimo_valor(self):
        self.assertEqual(
            _get_retry_countdown(99),
            2 * 60 * 60,
        )


class BillyClientTests(SimpleTestCase):
    def make_client(
        self,
        rate_limiter=None,
    ):
        return BillyClient(
            token="test-token",
            rate_limiter=(
                rate_limiter
                or FakeRateLimiter()
            ),
        )

    def test_get_invoice_usa_v3(self):
        client = self.make_client()

        response = FakeResponse(
            status_code=200,
            payload={
                "data": {
                    "cufe": "ABC",
                }
            },
        )

        client.session.request = MagicMock(
            return_value=response
        )

        result = client.get_invoice_by_cufe(
            "ABC"
        )

        self.assertEqual(
            result["data"]["cufe"],
            "ABC",
        )

        client.session.request.assert_called_once()

        call = client.session.request.call_args

        self.assertEqual(
            call.kwargs["method"],
            "GET",
        )

        self.assertTrue(
            call.kwargs["url"].endswith(
                "/v3/invoices"
            )
        )

        self.assertEqual(
            call.kwargs["params"],
            {
                "cufe": "ABC"
            },
        )

    def test_upload_409_es_estado_aceptado(self):
        client = self.make_client()

        response = FakeResponse(
            status_code=409,
        )

        client.session.request = MagicMock(
            return_value=response
        )

        result = (
            client.upload_invoice_by_cufe(
                "ABC"
            )
        )

        self.assertEqual(
            result.status_code,
            409,
        )

    def test_404_genera_not_found(self):
        client = self.make_client()

        client.session.request = MagicMock(
            return_value=FakeResponse(
                status_code=404,
            )
        )

        with self.assertRaises(
            BillyNotFoundError
        ):
            client.get_invoice_by_cufe(
                "ABC"
            )

    def test_429_genera_rate_limit(self):
        client = self.make_client()

        client.session.request = MagicMock(
            return_value=FakeResponse(
                status_code=429,
                headers={
                    "Retry-After": "60"
                },
            )
        )

        with self.assertRaises(
            BillyRateLimitError
        ) as ctx:
            client.get_invoice_by_cufe(
                "ABC"
            )

        self.assertEqual(
            ctx.exception.retry_after,
            "60",
        )

    def test_500_genera_billy_api_error(self):
        client = self.make_client()

        client.session.request = MagicMock(
            return_value=FakeResponse(
                status_code=500,
                payload={
                    "error": "server"
                },
            )
        )

        with self.assertRaises(
            BillyAPIError
        ) as ctx:
            client.get_invoice_by_cufe(
                "ABC"
            )

        self.assertEqual(
            ctx.exception.status_code,
            500,
        )

    def test_timeout_se_convierte_en_error_billy(self):
        client = self.make_client()

        client.session.request = MagicMock(
            side_effect=requests.exceptions.Timeout()
        )

        with self.assertRaises(
            BillyTimeoutError
        ):
            client.get_invoice_by_cufe(
                "ABC"
            )

    def test_rate_limit_local_evitar_request_http(self):
        client = self.make_client(
            FakeRateLimiter(
                allowed=False,
                retry_after=7,
                count=400,
                limit=400,
            )
        )

        client.session.request = MagicMock()

        with self.assertRaises(
            BillyLocalRateLimitError
        ) as ctx:
            client.get_invoice_by_cufe(
                "ABC"
            )

        self.assertEqual(
            ctx.exception.retry_after,
            7,
        )

        client.session.request.assert_not_called()


class BillyUploadServiceTests(
    SimpleTestCase
):
    def test_error_funcional_en_http_200_no_se_marca_como_exito(
        self,
    ):
        response = FakeResponse(
            status_code=200,
            payload={
                "errors": [
                    {
                        "status": "401",
                        "detail": (
                            "Token sin permisos"
                        ),
                    }
                ]
            },
        )

        code, detail = (
            BillyUploadService
            ._get_functional_result(
                response
            )
        )

        self.assertEqual(
            code,
            "401",
        )

        self.assertEqual(
            detail,
            "Token sin permisos",
        )

    def test_http_409_es_funcionalmente_valido(
        self,
    ):
        response = FakeResponse(
            status_code=409,
            payload={},
        )

        code, detail = (
            BillyUploadService
            ._get_functional_result(
                response
            )
        )

        self.assertEqual(
            code,
            "409",
        )

        self.assertIsNone(
            detail
        )

    @patch(
        "apps.bill.services.billy."
        "upload_service.BillyClient"
    )
    def test_upload_cufe_exitoso(
        self,
        client_class,
    ):
        client = (
            client_class.return_value
        )

        client.upload_invoice_by_cufe.return_value = (
            FakeResponse(
                status_code=201,
                payload={},
            )
        )

        result = (
            BillyUploadService()
            .upload_cufe(
                "ABC"
            )
        )

        self.assertTrue(
            result["ok"]
        )

        self.assertEqual(
            result["status"],
            "synced",
        )

        self.assertEqual(
            result["code"],
            "201",
        )

    @patch(
        "apps.bill.services.billy."
        "upload_service.BillyClient"
    )
    def test_upload_cufe_401_queda_pending(
        self,
        client_class,
    ):
        client = (
            client_class.return_value
        )

        from apps.bill.services.billy.exceptions import (
            BillyAuthenticationError,
        )

        client.upload_invoice_by_cufe.side_effect = (
            BillyAuthenticationError(
                "Token inválido"
            )
        )

        result = (
            BillyUploadService()
            .upload_cufe(
                "ABC"
            )
        )

        self.assertFalse(
            result["ok"]
        )

        self.assertEqual(
            result["status"],
            "pending",
        )

        self.assertEqual(
            result["code"],
            "401",
        )

    @patch(
        "apps.bill.services.billy."
        "upload_service.BillyClient"
    )
    def test_upload_cufe_timeout_es_error_transporte(
        self,
        client_class,
    ):
        client = (
            client_class.return_value
        )

        client.upload_invoice_by_cufe.side_effect = (
            BillyTimeoutError(
                "Billy timeout"
            )
        )

        result = (
            BillyUploadService()
            .upload_cufe(
                "ABC"
            )
        )

        self.assertFalse(
            result["ok"]
        )

        self.assertTrue(
            result[
                "transport_error"
            ]
        )


class BillySchedulerTests(
    SimpleTestCase
):
    @patch(
        "apps.bill.tasks."
        "sync_bill_events.delay"
    )
    @patch(
        "apps.bill.tasks.Bill"
    )
    def test_scheduler_reclama_antes_de_encolar(
        self,
        bill_model,
        delay,
    ):
        import apps.bill.tasks as tasks

        bill_id_1 = "bill-1"
        bill_id_2 = "bill-2"

        due_queryset = MagicMock()

        bill_model.objects.filter.return_value = (
            due_queryset
        )

        due_queryset.exclude.return_value = (
            due_queryset
        )

        due_queryset.order_by.return_value = (
            due_queryset
        )

        due_queryset.count.return_value = 2

        due_queryset.values_list.return_value.__getitem__.return_value = [
            bill_id_1,
            bill_id_2,
        ]

        claimed_queryset = MagicMock()

        # Después de construir el queryset
        # inicial, cada filter dentro del
        # for representa el claim.
        bill_model.objects.filter.side_effect = [
            due_queryset,
            claimed_queryset,
            claimed_queryset,
        ]

        claimed_queryset.update.return_value = 1

        with patch.object(
            tasks.settings,
            "BILLY_SCHEDULER_BATCH_SIZE",
            100,
            create=True,
        ):
            result = (
                tasks
                .schedule_due_billy_bills
                .run()
            )

        self.assertTrue(
            result["ok"]
        )

        self.assertEqual(
            result["scheduled"],
            2,
        )

        self.assertEqual(
            delay.call_count,
            2,
        )

    @patch(
        "apps.bill.tasks."
        "sync_bill_events.delay"
    )
    @patch(
        "apps.bill.tasks.Bill"
    )
    def test_scheduler_no_encola_si_claim_falla(
        self,
        bill_model,
        delay,
    ):
        import apps.bill.tasks as tasks

        due_queryset = MagicMock()
        claimed_queryset = MagicMock()

        bill_model.objects.filter.side_effect = [
            due_queryset,
            claimed_queryset,
        ]

        due_queryset.exclude.return_value = (
            due_queryset
        )

        due_queryset.order_by.return_value = (
            due_queryset
        )

        due_queryset.count.return_value = 1

        due_queryset.values_list.return_value.__getitem__.return_value = [
            "bill-1"
        ]

        claimed_queryset.update.return_value = 0

        with patch.object(
            tasks.settings,
            "BILLY_SCHEDULER_BATCH_SIZE",
            100,
            create=True,
        ):
            result = (
                tasks
                .schedule_due_billy_bills
                .run()
            )

        self.assertEqual(
            result["scheduled"],
            0,
        )

        delay.assert_not_called()