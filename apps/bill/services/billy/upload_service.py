import logging

from django.utils import timezone

from .client import BillyClient
from .exceptions import (
    BillyAPIError,
    BillyAuthenticationError,
    BillyConnectionError,
    BillyLocalRateLimitError,
    BillyNotFoundError,
    BillyRateLimitError,
    BillyTimeoutError,
)

logger = logging.getLogger(__name__)


class BillyUploadService:
    """Centraliza la carga manual de facturas a Billy por CUFE."""

    SUCCESS_CODES = {"200", "201", "409"}

    def upload_cufe(self, cufe, token=None):
        """
        Carga un CUFE en Billy sin requerir que la factura exista aún en BD.

        Se usa, por ejemplo, durante la lectura/importación de XML antes de
        crear el objeto Bill local.
        """
        if not cufe:
            return {
                "ok": False,
                "status": "not_requested",
                "code": None,
                "detail": "Factura sin CUFE",
                "transport_error": False,
            }

        client = BillyClient(token=token) if token else BillyClient()

        try:
            response = client.upload_invoice_by_cufe(cufe)
            code, detail = self._get_functional_result(response)
            ok = code in self.SUCCESS_CODES

            return {
                "ok": ok,
                "status": "synced" if ok else "pending",
                "code": code,
                "detail": detail,
                "transport_error": False,
            }

        except BillyAuthenticationError as exc:
            return self._error_result("401", exc)

        except BillyNotFoundError as exc:
            return self._error_result("404", exc)

        except BillyRateLimitError as exc:
            return self._error_result("429", exc)

        except BillyLocalRateLimitError as exc:
            return self._error_result("local_rate_limit", exc)

        except BillyTimeoutError as exc:
            return self._error_result(
                "timeout",
                exc,
                transport_error=True,
            )

        except BillyConnectionError as exc:
            return self._error_result(
                "connection_error",
                exc,
                transport_error=True,
            )

        except BillyAPIError as exc:
            return self._error_result(
                str(exc.status_code or "billy_api_error"),
                exc,
            )

    def upload_bill(self, bill, token=None, token_scope="smart"):
        """
        Carga una factura existente y persiste el estado del intento en Bill.
        """
        if not bill.cufe:
            return {
                "ok": False,
                "status": "not_requested",
                "code": None,
                "detail": "Factura sin CUFE",
                "transport_error": False,
            }

        result = self.upload_cufe(
            bill.cufe,
            token=token,
        )

        bill.billySyncAttempts = (bill.billySyncAttempts or 0) + 1
        bill.billyLastSyncAt = timezone.now()
        bill.billyTokenScope = token_scope

        if result["ok"]:
            bill.billySyncStatus = "synced"
            bill.billyErrorCode = None
            bill.billyErrorDetail = None
        else:
            bill.billySyncStatus = "pending"
            bill.billyErrorCode = result.get("code")
            bill.billyErrorDetail = result.get("detail")

        bill.save(
            update_fields=[
                "billySyncStatus",
                "billyErrorCode",
                "billyErrorDetail",
                "billySyncAttempts",
                "billyLastSyncAt",
                "billyTokenScope",
                "updated_at",
            ]
        )

        return {
            **result,
            "status": bill.billySyncStatus,
        }

    @staticmethod
    def _get_functional_result(response):
        """
        Billy puede responder HTTP 200 y reportar un error funcional en
        ``errors``. Conservamos ese comportamiento del flujo legacy.
        """
        try:
            payload = response.json()
        except ValueError:
            payload = {}

        errors = (
            payload.get("errors", [])
            if isinstance(payload, dict)
            else []
        )
        error = (
            errors[0]
            if errors and isinstance(errors[0], dict)
            else {}
        )

        code = str(
            error.get("status")
            or response.status_code
        )

        detail = (
            error.get("detail")
            or error.get("title")
            or None
        )

        return code, detail

    @staticmethod
    def _error_result(code, exc, transport_error=False):
        logger.warning(
            "Billy upload failed code=%s error=%s",
            code,
            str(exc),
        )

        return {
            "ok": False,
            "status": "pending",
            "code": str(code),
            "detail": str(exc),
            "transport_error": transport_error,
        }
