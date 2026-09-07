import logging

import environ
import requests

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

logger = logging.getLogger(__name__)

env = environ.Env()


class BillyClient:
    BASE_URL = "https://api.billy.com.co"

    def __init__(
        self,
        token=None,
        timeout=5,
        rate_limiter=None,
    ):
        self.token = token or env("SMART_TOKEN")
        self.timeout = timeout

        self.rate_limiter = (
            rate_limiter
            or BillyRateLimiter()
        )

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
        )

    def _request(self, method, path, expected_statuses=(200,), **kwargs):
        url = f"{self.BASE_URL}{path}"

        timeout = kwargs.pop("timeout", self.timeout)

        rate = self.rate_limiter.acquire()

        if not rate["allowed"]:
            raise BillyLocalRateLimitError(
                "Se alcanzó el límite interno de solicitudes a Billy",
                retry_after=rate["retry_after"],
                count=rate["count"],
                limit=rate["limit"],
            )

        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=timeout,
                **kwargs,
            )

        except requests.exceptions.Timeout as exc:
            logger.warning(
                "Billy timeout method=%s path=%s",
                method,
                path,
            )
            raise BillyTimeoutError(
                f"Timeout consultando Billy: {path}"
            ) from exc

        except requests.exceptions.RequestException as exc:
            logger.error(
                "Billy network error method=%s path=%s error=%s",
                method,
                path,
                str(exc),
            )
            raise BillyConnectionError(
                f"Error de conexión consultando Billy: {path}"
            ) from exc

        if response.status_code in expected_statuses:
            return response

        if response.status_code in (401, 403):
            raise BillyAuthenticationError(
                f"Billy rechazó la autenticación ({response.status_code})"
            )

        if response.status_code == 404:
            raise BillyNotFoundError(
                f"Recurso no encontrado en Billy: {path}"
            )

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")

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