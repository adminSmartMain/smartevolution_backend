from django.test import SimpleTestCase, override_settings
from prometheus_client import CollectorRegistry, generate_latest

from apps.bill.services.billy.metrics import BillyMetricsRecorder, BillyRedisCollector


class FakePipeline:
    def __init__(self, redis):
        self.redis = redis
        self.ops = []

    def hincrby(self, key, field, amount):
        self.ops.append(("hincrby", key, field, amount))
        return self

    def set(self, key, value):
        self.ops.append(("set", key, value))
        return self

    def execute(self):
        result = []
        for op in self.ops:
            if op[0] == "hincrby":
                result.append(self.redis.hincrby(*op[1:]))
            else:
                result.append(self.redis.set(*op[1:]))
        return result


class FakeRedis:
    def __init__(self):
        self.hashes = {}
        self.values = {}
        self.ttls = {}

    def _hash(self, key):
        return self.hashes.setdefault(key, {})

    def hincrby(self, key, field, amount):
        data = self._hash(key)
        data[field] = int(data.get(field, 0)) + int(amount)
        return data[field]

    def hincrbyfloat(self, key, field, amount):
        data = self._hash(key)
        data[field] = float(data.get(field, 0)) + float(amount)
        return data[field]

    def hgetall(self, key):
        return dict(self.hashes.get(key, {}))

    def set(self, key, value, **kwargs):
        self.values[key] = str(value)
        if "ex" in kwargs:
            self.ttls[key] = int(kwargs["ex"])
        return True

    def get(self, key):
        return self.values.get(key)

    def ttl(self, key):
        return self.ttls.get(key, -2)

    def pipeline(self):
        return FakePipeline(self)


class BillyPrometheusMetricsTests(SimpleTestCase):
    def setUp(self):
        self.redis = FakeRedis()
        self.metrics = BillyMetricsRecorder(redis_client=self.redis)

    def test_http_attempt_and_response_are_counted_by_origin(self):
        self.metrics.record_http_attempt("GET", "get_invoice_by_cufe", "worker")
        self.metrics.record_http_response("GET", "get_invoice_by_cufe", "worker", 200)

        self.assertEqual(
            self.redis.hgetall(self.metrics.HTTP_ATTEMPTS_KEY)[
                "GET|get_invoice_by_cufe|worker"
            ],
            1,
        )
        self.assertEqual(
            self.redis.hgetall(self.metrics.HTTP_RESPONSES_KEY)[
                "GET|get_invoice_by_cufe|worker|200"
            ],
            1,
        )

    def test_local_rejection_is_separate_from_outbound_attempt(self):
        self.metrics.record_local_rejection(
            "get_invoice_by_cufe",
            "worker",
            "hour",
        )
        self.assertEqual(self.redis.hgetall(self.metrics.HTTP_ATTEMPTS_KEY), {})
        self.assertEqual(
            self.redis.hgetall(self.metrics.LOCAL_REJECTIONS_KEY)[
                "get_invoice_by_cufe|worker|hour"
            ],
            1,
        )

    @override_settings(
        BILLY_RATE_LIMIT_PER_MINUTE=400,
        BILLY_RATE_LIMIT_PER_HOUR=4000,
    )
    def test_collector_exposes_requests_budget_and_limits(self):
        self.metrics.record_http_attempt("GET", "get_invoice_by_cufe", "worker")
        self.metrics.record_scheduler(
            due_total=12,
            scheduled=8,
            minute_remaining=392,
            hour_remaining=3992,
        )

        registry = CollectorRegistry()
        registry.register(BillyRedisCollector(redis_client=self.redis))
        payload = generate_latest(registry).decode()

        self.assertIn('billy_http_attempts_total{method="GET",operation="get_invoice_by_cufe",origin="worker"} 1.0', payload)
        self.assertIn('billy_scheduler_due_bills 12.0', payload)
        self.assertIn('billy_budget_remaining{window="minute"} 392.0', payload)
        self.assertIn('billy_configured_rate_limit{window="hour"} 4000.0', payload)
