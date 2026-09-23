import logging
import time

import environ
import requests
from django.conf import settings

from .exceptions import (
    BillyAPIError,
    BillyAuthenticationError,
    BillyConnectionError,
    BillyLocalRateLimitError,
    BillyNotFoundError,
    BillyRateLimitError,
    BillyTimeoutError,
)
from .rate_limiter import BillyRateLimiter
from .metrics import BillyMetricsRecorder

logger = logging.getLogger(__name__)
env = environ.Env()


class BillyClient:
    BASE_URL = "https://api.billy.com.co"

    def __init__(self, token=None, timeout=5, rate_limiter=None, origin="unknown", metrics=None):
        self.token = token or env("SMART_TOKEN")
        self.timeout = timeout
        self.rate_limiter = rate_limiter or BillyRateLimiter()
        self.origin = origin
        self.metrics = metrics or BillyMetricsRecorder()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    def get_invoice_by_cufe(self, cufe):
        response = self._request(
            "GET",
            "/v3/invoices",
            expected_statuses=(200,),
            params={"cufe": cufe},
            _operation="get_invoice_by_cufe",
        )
        try:
            return response.json()
        except ValueError as exc:
            raise BillyAPIError(
                message="Billy respondió 200 pero el cuerpo no es JSON válido",
                status_code=response.status_code,
            ) from exc

    def upload_invoice_by_cufe(self, cufe):
        return self._request(
            "POST",
            "/v1/invoices/uploadByCufe",
            expected_statuses=(200, 201, 409),
            json={"cufe": cufe},
            timeout=30,
            _operation="upload_invoice_by_cufe",
        )

    def _request(self, method, path, expected_statuses=(200,), **kwargs):
        url = f"{self.BASE_URL}{path}"
        timeout = kwargs.pop("timeout", self.timeout)
        operation = kwargs.pop("_operation", path.strip("/").replace("/", "_"))

        # Esta adquisición es el guardrail duro. Todas las vías (web,
        # workers, uploads) pasan por el mismo Redis y comparten 400/min
        # + 4000/h. Si no hay presupuesto, no sale tráfico HTTP.
        rate = self.rate_limiter.acquire()
        if not rate["allowed"]:
            self.metrics.record_local_rejection(operation, self.origin, rate.get("scope"))
            raise BillyLocalRateLimitError(
                "Billy bloqueado por guardrail interno",
                retry_after=rate["retry_after"],
                count=rate.get("count"),
                limit=rate.get("limit"),
                scope=rate.get("scope"),
            )

        self.metrics.record_http_attempt(method, operation, self.origin)
        started_at = time.monotonic()
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=timeout,
                **kwargs,
            )
        except requests.exceptions.Timeout as exc:
            self.metrics.record_duration(method, operation, self.origin, time.monotonic() - started_at)
            self.metrics.record_transport_error(method, operation, self.origin, "timeout")
            logger.warning("Billy timeout method=%s path=%s", method, path)
            raise BillyTimeoutError(f"Timeout consultando Billy: {path}") from exc
        except requests.exceptions.RequestException as exc:
            self.metrics.record_duration(method, operation, self.origin, time.monotonic() - started_at)
            self.metrics.record_transport_error(method, operation, self.origin, "connection_error")
            logger.error(
                "Billy network error method=%s path=%s error=%s",
                method,
                path,
                str(exc),
            )
            raise BillyConnectionError(
                f"Error de conexión consultando Billy: {path}"
            ) from exc

        self.metrics.record_duration(method, operation, self.origin, time.monotonic() - started_at)
        self.metrics.record_http_response(method, operation, self.origin, response.status_code)

        if response.status_code in expected_statuses:
            return response

        if response.status_code in (401, 403):
            # Mismo token para todos los procesos: si autenticación falla,
            # evitamos que miles de tareas repitan el mismo error mientras
            # se corrige el acceso.
            auth_block = getattr(settings, "BILLY_AUTH_GLOBAL_BLOCK_SECONDS", 15 * 60)
            self.rate_limiter.block_global(auth_block, reason="authentication")
            self.metrics.record_global_block("authentication")
            raise BillyAuthenticationError(
                f"Billy rechazó la autenticación ({response.status_code})"
            )

        if response.status_code == 404:
            raise BillyNotFoundError(f"Recurso no encontrado en Billy: {path}")

        if response.status_code == 429:
            retry_after = self.rate_limiter.parse_retry_after(
                response.headers.get("Retry-After"),
                default=60,
            )
            # 429 no es un error de una factura: es un bloqueo compartido.
            # Persistimos el Retry-After en Redis para que scheduler, web y
            # todos los workers dejen de llamar inmediatamente.
            self.rate_limiter.block_global(retry_after, reason="429")
            self.metrics.record_global_block("429")
            raise BillyRateLimitError(
                "Billy alcanzó el límite de solicitudes",
                retry_after=retry_after,
            )

        try:
            response_data = response.json()
        except ValueError:
            response_data = None

        raise BillyAPIError(
            message=f"Billy respondió HTTP {response.status_code}",
            status_code=response.status_code,
            response_data=response_data,
        )
