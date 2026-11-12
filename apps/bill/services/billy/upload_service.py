import logging

from django.utils import timezone

from .client import BillyClient
from .exceptions import (
    BillyAPIError,
    BillyAuthenticationError,
    BillyAuthenticationGuardrailError,
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

            if not ok:
                # Billy puede informar errores funcionales dentro de HTTP 200.
                # Los normalizamos igual que los errores HTTP para no filtrar
                # detalles del proveedor ni obligar al frontend a interpretar
                # códigos HTTP en el body.
                if code == "401":
                    return self._functional_error_result(
                        "authentication_rejected", code,
                        "Billy rechazó las credenciales configuradas.", False,
                    )
                if code == "429":
                    return self._functional_error_result(
                        "provider_rate_limit", code,
                        "Billy limitó temporalmente las solicitudes.", True,
                    )
                return self._functional_error_result(
                    "provider_request_rejected", code,
                    "Billy rechazó la solicitud.", False,
                )

            return {
                "ok": ok,
                "status": "synced" if ok else "pending",
                "code": code,
                "detail": detail,
                "transport_error": False,
                "error_code": None,
                "retryable": False,
                "retry_after": None,
            }

        except BillyAuthenticationError as exc:
            return self._error_result(
                "authentication_rejected", exc, retryable=False,
                message="Billy rechazó las credenciales configuradas.",
            )

        except BillyAuthenticationGuardrailError as exc:
            return self._error_result(
                "authentication_guardrail_active", exc,
                retryable=True, retry_after=exc.retry_after,
                message="La integración con Billy está temporalmente bloqueada por autenticación.",
            )

        except BillyNotFoundError as exc:
            return self._error_result("404", exc)

        except BillyRateLimitError as exc:
            return self._error_result(
                "provider_rate_limit", exc, retryable=True,
                retry_after=exc.retry_after,
                message="Billy limitó temporalmente las solicitudes.",
            )

        except BillyLocalRateLimitError as exc:
            return self._error_result(
                "local_rate_limit", exc, retryable=True,
                retry_after=exc.retry_after,
                message="La capacidad local de Billy está temporalmente agotada.",
            )

        except BillyTimeoutError as exc:
            return self._error_result(
                "timeout",
                exc,
                transport_error=True, retryable=True,
                message="Billy no respondió a tiempo.",
            )

        except BillyConnectionError as exc:
            return self._error_result(
                "connection_error",
                exc,
                transport_error=True, retryable=True,
                message="No fue posible conectar con Billy.",
            )

        except BillyAPIError as exc:
            if exc.status_code and exc.status_code >= 500:
                return self._error_result(
                    "provider_unavailable", exc, retryable=True,
                    message="Billy no está disponible temporalmente.",
                )
            return self._error_result(
                "provider_api_error",
                exc,
                message="Billy respondió con un error no esperado.",
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
    def _functional_error_result(error_code, provider_status, message, retryable):
        return {
            "ok": False,
            "status": "pending",
            "code": error_code,
            "provider_status": str(provider_status),
            "detail": message,
            "transport_error": False,
            "error_code": error_code,
            "retryable": retryable,
            "retry_after": None,
        }

    @staticmethod
    def _error_result(
        code, exc, transport_error=False, retryable=False, retry_after=None,
        message=None,
    ):
        logger.warning("Billy upload failed code=%s error_type=%s", code, type(exc).__name__)

        return {
            "ok": False,
            "status": "pending",
            "code": str(code),
            "provider_status": None,
            # Nunca se devuelve el texto del proveedor: puede contener
            # contexto sensible. El detalle completo queda solo en logs.
            "detail": message or "No fue posible completar la operación con Billy.",
            "transport_error": transport_error,
            "error_code": str(code),
            "retryable": retryable,
            "retry_after": retry_after,
        }
