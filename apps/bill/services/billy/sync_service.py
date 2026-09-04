import logging

from django.db import transaction

from apps.misc.api.models.typeBill.index import TypeBill
from apps.bill.utils.events import normalize_description, ts_to_datetime
from apps.bill.utils.updateMassiveTypeBill import (
    compute_type_bill_from_events,
    sync_bill_events_v2,
)

from .client import BillyClient
from .normalizer import BillyInvoiceNormalizer


logger = logging.getLogger(__name__)


class BillySyncService:
    def __init__(self, client=None):
        self.client = client or BillyClient()

    @transaction.atomic
    def sync_bill(self, bill):
        """
        Sincroniza una factura local contra Billy.

        Responsabilidades:
        - consultar Billy
        - normalizar respuesta v3
        - convertir eventos al formato interno actual
        - persistir nuevos BillEvent
        - actualizar currentOwner
        - recalcular typeBill

        No maneja retries, locks ni rate limiting.
        Eso corresponde a Celery/Redis.
        """

        if not bill.cufe:
            return {
                "ok": False,
                "reason": "missing_cufe",
                "events_created": 0,
                "owner_changed": False,
                "type_changed": False,
            }

        logger.info(
            "Synchronizing bill with Billy bill_id=%s cufe=%s",
            bill.id,
            bill.cufe,
        )

        payload = self.client.get_invoice_by_cufe(bill.cufe)

        invoice = BillyInvoiceNormalizer.normalize(payload)

        api_events = self._parse_events(invoice)

        owner_changed = self._update_owner(
            bill,
            invoice.current_owner,
        )

        events_created = sync_bill_events_v2(
            bill,
            api_events,
        )

        type_changed = self._update_type_bill(
            bill,
            api_events,
        )

        logger.info(
            "Billy synchronization completed "
            "bill_id=%s events_created=%s "
            "owner_changed=%s type_changed=%s",
            bill.id,
            events_created,
            owner_changed,
            type_changed,
        )

        return {
            "ok": True,
            "bill_id": str(bill.id),
            "cufe": bill.cufe,
            "status": invoice.status,
            "events_last_update": invoice.events_last_update,
            "events_received": len(api_events),
            "events_created": events_created,
            "owner_changed": owner_changed,
            "type_changed": type_changed,
        }

    def _parse_events(self, invoice):
        parsed_events = []

        for event in invoice.events:
            code = event.code

            for detail in event.details:
                description = (
                    detail.get("description", "") or ""
                )

                parsed_events.append(
                    {
                        "code": code,
                        "description": description,
                        "description_norm": normalize_description(
                            description
                        ),
                        "date": ts_to_datetime(
                            detail.get("timestamp")
                        ),
                    }
                )

        return parsed_events

    def _update_owner(self, bill, current_owner):
        current_owner = (current_owner or "").strip()

        if not current_owner:
            return False

        previous_owner = (
            getattr(bill, "currentOwner", "") or ""
        ).strip()

        if current_owner == previous_owner:
            return False

        bill.currentOwner = current_owner
        bill.save(update_fields=["currentOwner"])

        logger.info(
            "Billy current owner changed bill_id=%s old=%s new=%s",
            bill.id,
            previous_owner,
            current_owner,
        )

        return True

    def _update_type_bill(self, bill, api_events):
        new_type_id = compute_type_bill_from_events(
            api_events
        )

        if not new_type_id:
            return False

        if str(bill.typeBill_id) == str(new_type_id):
            return False

        if not TypeBill.objects.filter(
            id=new_type_id
        ).exists():
            logger.error(
                "Billy calculated typeBill does not exist "
                "bill_id=%s type_bill=%s",
                bill.id,
                new_type_id,
            )
            return False

        old_type_id = bill.typeBill_id

        bill.typeBill_id = new_type_id
        bill.save(update_fields=["typeBill"])

        logger.info(
            "Billy typeBill changed bill_id=%s old=%s new=%s",
            bill.id,
            old_type_id,
            new_type_id,
        )

        return True