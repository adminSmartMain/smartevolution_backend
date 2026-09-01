import logging

from apps.base.exceptions import HttpException
from .events import normalize_description, ts_to_datetime


from apps.bill.services.billy.exceptions import (
    BillyAPIError,
    BillyAuthenticationError,
    BillyConnectionError,
    BillyNotFoundError,
    BillyRateLimitError,
    BillyTimeoutError,
)
from apps.bill.services.billy import BillyClient, BillyInvoiceNormalizer

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


UUID_FV = "fdb5feb4-24e9-41fc-9689-31aff60b76c9"
UUID_FV_TV = "a7c70741-8c1a-4485-8ed4-5297e54a978a"
UUID_RECHAZADA = "dcec6f03-5dc1-42ea-a525-afada28686da"
UUID_ENDOSADA = "29113618-6ab8-4633-aa8e-b3d6f242e8a4"
UUID_PAGADA = "e079bea4-401e-41f2-8ccc-e4ac42217728"


def billEvents(cufe, update=False):
    try:
        logger.debug(
            "Fetching bill events for CUFE: %s",
            cufe,
        )

        billy_client = BillyClient()

        

        bill_data = billy_client.get_invoice_by_cufe(cufe)

        invoice = BillyInvoiceNormalizer.normalize(bill_data)

        events_api = invoice.events
        current_owner = invoice.current_owner
        current_owner_id = invoice.current_owner_id

        codes = {event.code for event in events_api}

        is_reject = "031" in codes
        is_pagada = any(c in codes for c in ["045", "051"])
        is_endosada = any(c in codes for c in ["037", "047", "046"])
        is_fv_tv = (
            "030" in codes
            and "032" in codes
            and ("033" in codes or "034" in codes)
        )

        parsed_events = []

        for event in events_api:
            code = event.code

            if code in ["036", "037", "038", "046"] and not update:
                continue

            details = event.details

            if not details:
                continue

            for detail in details:
                description = detail.get("description", "") or ""
                date = ts_to_datetime(detail.get("timestamp"))

                parsed_events.append({
                    "code": code,
                    "description": description,
                    "description_norm": normalize_description(description),
                    "date": date,
                })

        # IMPORTANTE: esto va fuera del for
        if is_reject:
            response_type = UUID_RECHAZADA
        elif is_pagada:
            response_type = UUID_PAGADA
        elif is_endosada:
            response_type = UUID_ENDOSADA
        elif is_fv_tv:
            response_type = UUID_FV_TV
        else:
            response_type = UUID_FV

        return {
            "ok": True,
            "type": response_type,
            "events": parsed_events,
            "currentOwner": current_owner,
            "current_ownerId": current_owner_id,
            "bill": bill_data,
            "warning": None,
        }

    except BillyTimeoutError:
        logger.warning(
            "Timeout fetching bill events for CUFE: %s",
            cufe,
        )

        return {
            "ok": False,
            "error": "billy_timeout",
            "warning": "Billy está lento. Los eventos no se pudieron actualizar.",
            "type": None,
            "events": None,
            "currentOwner": None,
            "current_ownerId": None,
            "bill": None,
        }

    except BillyConnectionError as exc:
        logger.error(
            "Network error for CUFE %s: %s",
            cufe,
            str(exc),
        )

        return {
            "ok": False,
            "error": "billy_network_error",
            "warning": "Error de red consultando Billy.",
            "type": None,
            "events": None,
            "currentOwner": None,
            "current_ownerId": None,
            "bill": None,
        }

    except BillyAuthenticationError:
        logger.error(
            "Billy authentication error for CUFE %s",
            cufe,
        )

        return {
            "ok": False,
            "error": "billy_authentication_error",
            "warning": "Billy rechazó la autenticación.",
            "type": None,
            "events": None,
            "currentOwner": None,
            "current_ownerId": None,
            "bill": None,
        }

    except BillyRateLimitError as exc:
        logger.warning(
            "Billy rate limit reached for CUFE %s retry_after=%s",
            cufe,
            exc.retry_after,
        )

        return {
            "ok": False,
            "error": "billy_rate_limit",
            "retry_after": exc.retry_after,
            "warning": "Billy alcanzó temporalmente el límite de solicitudes.",
            "type": None,
            "events": None,
            "currentOwner": None,
            "current_ownerId": None,
            "bill": None,
        }

    except BillyNotFoundError:
        logger.warning(
            "Billy invoice not found for CUFE %s",
            cufe,
        )

        return {
            "ok": False,
            "error": "billy_not_found",
            "warning": "Billy no encontró la factura.",
            "type": None,
            "events": None,
            "currentOwner": None,
            "current_ownerId": None,
            "bill": None,
        }

    except BillyAPIError as exc:
        logger.error(
            "Billy API error for CUFE %s status=%s",
            cufe,
            exc.status_code,
        )

        return {
            "ok": False,
            "error": "billy_api_error",
            "status_code": exc.status_code,
            "warning": "Billy respondió con un error.",
            "type": None,
            "events": None,
            "currentOwner": None,
            "current_ownerId": None,
            "bill": None,
        }

    except Exception as exc:
        logger.exception(
            "Unexpected error for CUFE %s",
            cufe,
        )
        raise HttpException(str(exc))