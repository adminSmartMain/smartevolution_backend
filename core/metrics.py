from django.http import HttpResponse
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, generate_latest

from apps.bill.services.billy.metrics import BillyRedisCollector


def prometheus_metrics(request):
    """Endpoint interno scrapeable por Prometheus.

    Las métricas Billy se leen desde Redis, por lo que representan web +
    worker-billy + beat-billy sin depender del PID del proceso Gunicorn que
    atienda este request.
    """
    registry = CollectorRegistry()
    registry.register(BillyRedisCollector())
    return HttpResponse(
        generate_latest(registry),
        content_type=CONTENT_TYPE_LATEST,
    )
