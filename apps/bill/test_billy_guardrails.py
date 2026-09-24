from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from apps.bill.services.billy.polling import (
    calculate_next_check,
    calculate_bill_next_check,
    filter_eligible_for_billy_polling,
    is_bill_eligible_for_billy_polling,
)
from apps.bill.services.billy.rate_limiter import BillyRateLimiter
from apps.bill.tasks import _get_not_found_countdown
from apps.bill.utils.updateMassiveTypeBill import UUID_ENDOSADA, UUID_FV


class BillyGuardrailPollingTests(SimpleTestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 22, 12, 0, 0)

    def test_watchlist_preserva_cadencia_15_minutos_aunque_haya_streak(self):
        result = calculate_next_check(
            UUID_FV,
            self.now,
            on_watchlist=True,
            unchanged_streak=99,
        )
        self.assertEqual(result, self.now + timedelta(minutes=15))

    def test_endosada_preserva_24_horas(self):
        result = calculate_next_check(
            UUID_ENDOSADA,
            self.now,
            unchanged_streak=99,
        )
        self.assertEqual(result, self.now + timedelta(hours=24))

    def test_factura_activa_sin_cambios_se_enfria_gradualmente(self):
        expected = (3, 6, 12, 24, 24)
        for streak, hours in enumerate(expected, start=1):
            with self.subTest(streak=streak):
                self.assertEqual(
                    calculate_next_check(
                        UUID_FV,
                        self.now,
                        unchanged_streak=streak,
                    ),
                    self.now + timedelta(hours=hours),
                )

    def test_404_backoff_es_15m_30m_1h_3h_6h_12h_24h(self):
        expected = (900, 1800, 3600, 10800, 21600, 43200, 86400, 86400)
        self.assertEqual(
            tuple(_get_not_found_countdown(i) for i in range(1, 9)),
            expected,
        )

    @patch("apps.bill.services.billy.polling.apps.get_model")
    def test_watchlist_es_override_de_elegibilidad(self, get_model):
        bill = MagicMock(onWatchlist=True)
        self.assertTrue(is_bill_eligible_for_billy_polling(bill))
        get_model.assert_not_called()

    @patch("apps.bill.services.billy.polling.apps.get_model")
    def test_sin_operacion_es_elegible_y_conserva_reglas_normales(self, get_model):
        operations = MagicMock()
        operations.exists.return_value = False
        model = MagicMock()
        model.objects.filter.return_value = operations
        get_model.return_value = model

        bill = MagicMock(onWatchlist=False, id="bill-1")
        self.assertTrue(is_bill_eligible_for_billy_polling(bill))


    @patch("apps.bill.services.billy.polling.apps.get_model")
    def test_sin_operacion_se_programa_cada_24_horas(self, get_model):
        operations = MagicMock()
        operations.exists.return_value = False
        model = MagicMock()
        model.objects.filter.return_value = operations
        get_model.return_value = model

        bill = MagicMock(
            onWatchlist=False,
            id="bill-1",
            typeBill_id=UUID_FV,
        )
        self.assertEqual(
            calculate_bill_next_check(bill, self.now),
            self.now + timedelta(hours=24),
        )

    @patch("apps.bill.services.billy.polling.apps.get_model")
    def test_sin_operacion_en_watchlist_conserva_15_minutos(self, get_model):
        bill = MagicMock(
            onWatchlist=True,
            id="bill-1",
            typeBill_id=UUID_FV,
        )
        self.assertEqual(
            calculate_bill_next_check(bill, self.now),
            self.now + timedelta(minutes=15),
        )
        get_model.assert_not_called()

    @patch("apps.bill.services.billy.polling.apps.get_model")
    def test_todas_las_operaciones_status_4_no_es_elegible(self, get_model):
        operations = MagicMock()
        operations.exists.return_value = True
        operations.exclude.return_value.exists.return_value = False
        model = MagicMock()
        model.objects.filter.return_value = operations
        get_model.return_value = model

        bill = MagicMock(onWatchlist=False, id="bill-1")
        self.assertFalse(is_bill_eligible_for_billy_polling(bill))

    @patch("apps.bill.services.billy.polling.apps.get_model")
    def test_al_menos_una_operacion_status_distinto_4_es_elegible(self, get_model):
        operations = MagicMock()
        operations.exists.return_value = True
        operations.exclude.return_value.exists.return_value = True
        model = MagicMock()
        model.objects.filter.return_value = operations
        get_model.return_value = model

        bill = MagicMock(onWatchlist=False, id="bill-1")
        self.assertTrue(is_bill_eligible_for_billy_polling(bill))


class FakeRedis:
    def __init__(self, acquire_result=None, snapshot_result=None):
        self.acquire_result = acquire_result
        self.snapshot_result = snapshot_result
        self.calls = 0
        self.block = None

    def eval(self, script, numkeys, *args):
        self.calls += 1
        if "member = ARGV[5]" in script:
            return self.acquire_result
        return self.snapshot_result

    def set(self, key, value, ex=None, **kwargs):
        self.block = (key, value, ex)
        return True


class BillyGlobalBudgetTests(SimpleTestCase):
    def test_acquire_expone_ambas_ventanas(self):
        redis = FakeRedis(acquire_result=[1, 12, 321, 0, "allowed"])
        limiter = BillyRateLimiter(redis_client=redis, minute_limit=400, hour_limit=4000)
        result = limiter.acquire()
        self.assertTrue(result["allowed"])
        self.assertEqual(result["minute_count"], 12)
        self.assertEqual(result["hour_count"], 321)

    def test_presupuesto_horario_puede_detener_scheduler_aunque_minuto_tenga_margen(self):
        redis = FakeRedis(snapshot_result=[1, 10, 4000, 390, 0, "available"])
        limiter = BillyRateLimiter(redis_client=redis, minute_limit=400, hour_limit=4000)
        result = limiter.get_budget()
        self.assertTrue(result["available"])
        self.assertEqual(result["minute_remaining"], 390)
        self.assertEqual(result["hour_remaining"], 0)

    def test_global_block_guarda_retry_after(self):
        redis = FakeRedis()
        limiter = BillyRateLimiter(redis_client=redis)
        limiter.block_global(123, reason="429")
        self.assertEqual(redis.block[2], 123)
