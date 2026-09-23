import logging
import time

import redis
from django.conf import settings
from prometheus_client.core import (
    CounterMetricFamily,
    GaugeMetricFamily,
    SummaryMetricFamily,
)


logger = logging.getLogger(__name__)


class BillyMetricsRecorder:
    """Métricas Billy compartidas por todos los procesos mediante Redis.

    No usamos el modo multiprocess de prometheus_client porque web, Celery y
    Beat viven en contenedores distintos. Redis ya es un punto compartido y
    evita colisiones de PID entre contenedores.

    La telemetría es *best effort*: un fallo de métricas nunca debe bloquear
    una operación de negocio ni alterar los guardrails de Billy.
    """

    HTTP_ATTEMPTS_KEY = "billy:metrics:http_attempts"
    HTTP_RESPONSES_KEY = "billy:metrics:http_responses"
    TRANSPORT_ERRORS_KEY = "billy:metrics:transport_errors"
    LOCAL_REJECTIONS_KEY = "billy:metrics:local_rejections"
    RETRIES_KEY = "billy:metrics:retries"
    DEFERRALS_KEY = "billy:metrics:deferrals"
    GLOBAL_BLOCKS_KEY = "billy:metrics:global_blocks"
    SCHEDULER_KEY = "billy:metrics:scheduler"
    DURATION_COUNT_KEY = "billy:metrics:duration_count"
    DURATION_SUM_KEY = "billy:metrics:duration_sum"

    DUE_GAUGE_KEY = "billy:metrics:gauge:due"
    MINUTE_REMAINING_KEY = "billy:metrics:gauge:minute_remaining"
    HOUR_REMAINING_KEY = "billy:metrics:gauge:hour_remaining"
    LAST_SCHEDULER_TS_KEY = "billy:metrics:gauge:last_scheduler_ts"

    SEP = "|"

    def __init__(self, redis_client=None):
        self.redis = redis_client or redis.Redis.from_url(
            settings.CELERY_BROKER_URL,
            decode_responses=True,
        )

    @classmethod
    def _field(cls, *parts):
        return cls.SEP.join(str(part or "unknown") for part in parts)

    def _safe(self, operation, *args, **kwargs):
        try:
            return operation(*args, **kwargs)
        except redis.RedisError:
            logger.exception("Could not persist Billy Prometheus metrics")
            return None

    def record_http_attempt(self, method, operation, origin):
        self._safe(
            self.redis.hincrby,
            self.HTTP_ATTEMPTS_KEY,
            self._field(method, operation, origin),
            1,
        )

    def record_http_response(self, method, operation, origin, status):
        self._safe(
            self.redis.hincrby,
            self.HTTP_RESPONSES_KEY,
            self._field(method, operation, origin, status),
            1,
        )

    def record_transport_error(self, method, operation, origin, reason):
        self._safe(
            self.redis.hincrby,
            self.TRANSPORT_ERRORS_KEY,
            self._field(method, operation, origin, reason),
            1,
        )

    def record_local_rejection(self, operation, origin, scope):
        self._safe(
            self.redis.hincrby,
            self.LOCAL_REJECTIONS_KEY,
            self._field(operation, origin, scope),
            1,
        )

    def record_retry(self, reason):
        self._safe(
            self.redis.hincrby,
            self.RETRIES_KEY,
            self._field(reason),
            1,
        )

    def record_deferral(self, reason):
        self._safe(
            self.redis.hincrby,
            self.DEFERRALS_KEY,
            self._field(reason),
            1,
        )

    def record_global_block(self, reason):
        self._safe(
            self.redis.hincrby,
            self.GLOBAL_BLOCKS_KEY,
            self._field(reason),
            1,
        )

    def record_duration(self, method, operation, origin, seconds):
        field = self._field(method, operation, origin)
        self._safe(self.redis.hincrby, self.DURATION_COUNT_KEY, field, 1)
        self._safe(
            self.redis.hincrbyfloat,
            self.DURATION_SUM_KEY,
            field,
            max(float(seconds), 0.0),
        )

    def record_scheduler(
        self,
        *,
        due_total,
        scheduled,
        minute_remaining,
        hour_remaining,
        reason="completed",
        deduplicated=0,
    ):
        try:
            pipe = self.redis.pipeline()
            pipe.hincrby(self.SCHEDULER_KEY, "runs", 1)
            pipe.hincrby(self.SCHEDULER_KEY, "scheduled", int(scheduled or 0))
            pipe.hincrby(
                self.SCHEDULER_KEY,
                self._field("outcome", reason),
                1,
            )
            if deduplicated:
                pipe.hincrby(
                    self.SCHEDULER_KEY,
                    "deduplicated",
                    int(deduplicated),
                )
            pipe.set(self.DUE_GAUGE_KEY, int(due_total or 0))
            pipe.set(
                self.MINUTE_REMAINING_KEY,
                max(int(minute_remaining or 0), 0),
            )
            pipe.set(
                self.HOUR_REMAINING_KEY,
                max(int(hour_remaining or 0), 0),
            )
            pipe.set(self.LAST_SCHEDULER_TS_KEY, int(time.time()))
            pipe.execute()
        except redis.RedisError:
            logger.exception("Could not persist Billy scheduler metrics")


class BillyRedisCollector:
    """Prometheus collector que expone el estado acumulado guardado en Redis."""

    def __init__(self, redis_client=None):
        self.redis = redis_client or redis.Redis.from_url(
            settings.CELERY_BROKER_URL,
            decode_responses=True,
        )

    @staticmethod
    def _split(field, size):
        parts = str(field).split(BillyMetricsRecorder.SEP)
        return (parts + ["unknown"] * size)[:size]

    def _hgetall(self, key):
        return self.redis.hgetall(key) or {}

    def _get_float(self, key, default=0.0):
        value = self.redis.get(key)
        if value in (None, ""):
            return float(default)
        return float(value)

    def collect(self):
        redis_up = GaugeMetricFamily(
            "billy_metrics_redis_up",
            "1 si el collector puede leer las métricas Billy desde Redis.",
        )

        try:
            attempts = self._hgetall(BillyMetricsRecorder.HTTP_ATTEMPTS_KEY)
            responses = self._hgetall(BillyMetricsRecorder.HTTP_RESPONSES_KEY)
            transport_errors = self._hgetall(BillyMetricsRecorder.TRANSPORT_ERRORS_KEY)
            local_rejections = self._hgetall(BillyMetricsRecorder.LOCAL_REJECTIONS_KEY)
            retries = self._hgetall(BillyMetricsRecorder.RETRIES_KEY)
            deferrals = self._hgetall(BillyMetricsRecorder.DEFERRALS_KEY)
            global_blocks = self._hgetall(BillyMetricsRecorder.GLOBAL_BLOCKS_KEY)
            scheduler = self._hgetall(BillyMetricsRecorder.SCHEDULER_KEY)
            duration_count = self._hgetall(BillyMetricsRecorder.DURATION_COUNT_KEY)
            duration_sum = self._hgetall(BillyMetricsRecorder.DURATION_SUM_KEY)

            due = self._get_float(BillyMetricsRecorder.DUE_GAUGE_KEY)
            minute_remaining = self._get_float(BillyMetricsRecorder.MINUTE_REMAINING_KEY)
            hour_remaining = self._get_float(BillyMetricsRecorder.HOUR_REMAINING_KEY)
            last_scheduler_ts = self._get_float(BillyMetricsRecorder.LAST_SCHEDULER_TS_KEY)

            block_reason = self.redis.get("billy:rate:global_block") or "none"
            block_ttl = self.redis.ttl("billy:rate:global_block")
            if block_ttl is None or int(block_ttl) < 0:
                block_ttl = 0

            redis_up.add_metric([], 1)
        except (redis.RedisError, TypeError, ValueError):
            logger.exception("Could not collect Billy Prometheus metrics")
            redis_up.add_metric([], 0)
            yield redis_up
            return

        yield redis_up

        metric = CounterMetricFamily(
            "billy_http_attempts",
            "Solicitudes HTTP que Smart Evolution intentó enviar a Billy.",
            labels=["method", "operation", "origin"],
        )
        for field, value in attempts.items():
            metric.add_metric(self._split(field, 3), float(value))
        yield metric

        metric = CounterMetricFamily(
            "billy_http_responses",
            "Respuestas HTTP recibidas desde Billy.",
            labels=["method", "operation", "origin", "status"],
        )
        for field, value in responses.items():
            metric.add_metric(self._split(field, 4), float(value))
        yield metric

        metric = CounterMetricFamily(
            "billy_http_transport_errors",
            "Intentos HTTP sin respuesta por timeout o error de conexión.",
            labels=["method", "operation", "origin", "reason"],
        )
        for field, value in transport_errors.items():
            metric.add_metric(self._split(field, 4), float(value))
        yield metric

        metric = CounterMetricFamily(
            "billy_local_rate_limit_rejections",
            "Llamadas bloqueadas localmente antes de salir hacia Billy.",
            labels=["operation", "origin", "scope"],
        )
        for field, value in local_rejections.items():
            metric.add_metric(self._split(field, 3), float(value))
        yield metric

        metric = CounterMetricFamily(
            "billy_retries",
            "Retries técnicos Celery programados para Billy.",
            labels=["reason"],
        )
        for field, value in retries.items():
            metric.add_metric(self._split(field, 1), float(value))
        yield metric

        metric = CounterMetricFamily(
            "billy_polling_deferrals",
            "Pollings diferidos sin retry Celery.",
            labels=["reason"],
        )
        for field, value in deferrals.items():
            metric.add_metric(self._split(field, 1), float(value))
        yield metric

        metric = CounterMetricFamily(
            "billy_global_blocks",
            "Bloqueos globales Billy activados localmente.",
            labels=["reason"],
        )
        for field, value in global_blocks.items():
            metric.add_metric(self._split(field, 1), float(value))
        yield metric

        metric = SummaryMetricFamily(
            "billy_http_request_duration_seconds",
            "Duración de llamadas HTTP salientes hacia Billy.",
            labels=["method", "operation", "origin"],
        )
        all_duration_fields = set(duration_count) | set(duration_sum)
        for field in all_duration_fields:
            metric.add_metric(
                self._split(field, 3),
                count_value=float(duration_count.get(field, 0)),
                sum_value=float(duration_sum.get(field, 0)),
            )
        yield metric

        scheduler_runs = CounterMetricFamily(
            "billy_scheduler_runs",
            "Ejecuciones del scheduler Billy.",
        )
        scheduler_runs.add_metric([], float(scheduler.get("runs", 0)))
        yield scheduler_runs

        scheduler_scheduled = CounterMetricFamily(
            "billy_scheduler_scheduled",
            "Facturas encoladas por el scheduler Billy.",
        )
        scheduler_scheduled.add_metric([], float(scheduler.get("scheduled", 0)))
        yield scheduler_scheduled

        scheduler_deduplicated = CounterMetricFamily(
            "billy_scheduler_deduplicated",
            "Facturas que el scheduler no encoló por deduplicación Redis.",
        )
        scheduler_deduplicated.add_metric([], float(scheduler.get("deduplicated", 0)))
        yield scheduler_deduplicated

        scheduler_outcomes = CounterMetricFamily(
            "billy_scheduler_outcomes",
            "Resultados de ejecuciones del scheduler Billy.",
            labels=["outcome"],
        )
        for field, value in scheduler.items():
            if not str(field).startswith("outcome|"):
                continue
            scheduler_outcomes.add_metric(self._split(field, 2)[1:], float(value))
        yield scheduler_outcomes

        due_metric = GaugeMetricFamily(
            "billy_scheduler_due_bills",
            "Facturas elegibles vencidas vistas por el último scheduler.",
        )
        due_metric.add_metric([], due)
        yield due_metric

        budget_metric = GaugeMetricFamily(
            "billy_budget_remaining",
            "Presupuesto Billy restante según el último scheduler.",
            labels=["window"],
        )
        budget_metric.add_metric(["minute"], minute_remaining)
        budget_metric.add_metric(["hour"], hour_remaining)
        yield budget_metric

        configured_limit = GaugeMetricFamily(
            "billy_configured_rate_limit",
            "Límite interno configurado para Billy.",
            labels=["window"],
        )
        configured_limit.add_metric(
            ["minute"],
            float(getattr(settings, "BILLY_RATE_LIMIT_PER_MINUTE", 400)),
        )
        configured_limit.add_metric(
            ["hour"],
            float(getattr(settings, "BILLY_RATE_LIMIT_PER_HOUR", 4000)),
        )
        yield configured_limit

        block_active = GaugeMetricFamily(
            "billy_global_block_active",
            "1 cuando Billy está bloqueado globalmente por guardrail.",
            labels=["reason"],
        )
        block_active.add_metric([str(block_reason)], 1 if block_ttl > 0 else 0)
        yield block_active

        block_remaining = GaugeMetricFamily(
            "billy_global_block_seconds_remaining",
            "Segundos restantes del bloqueo global Billy.",
        )
        block_remaining.add_metric([], float(block_ttl))
        yield block_remaining

        last_run = GaugeMetricFamily(
            "billy_scheduler_last_run_timestamp_seconds",
            "Unix timestamp de la última ejecución observada del scheduler Billy.",
        )
        last_run.add_metric([], last_scheduler_ts)
        yield last_run
