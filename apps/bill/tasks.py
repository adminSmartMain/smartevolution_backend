import logging

from celery import shared_task

from apps.bill.models import Bill
from apps.bill.services.billy import (
    BillyLock,
    BillySyncService,
)


logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="apps.bill.tasks.sync_bill_events",
    queue="billy",
)
def sync_bill_events(self, bill_id):
    """
    Sincroniza una factura local contra Billy.

    La tarea Celery solo orquesta:
    - buscar la factura
    - validar que siga existiendo
    - validar que tenga CUFE
    - adquirir lock Redis por CUFE
    - delegar al BillySyncService
    - liberar el lock

    Retries y rate limiting se agregarán
    en commits posteriores.
    """

    logger.info(
        "Starting Billy sync task bill_id=%s task_id=%s",
        bill_id,
        self.request.id,
    )

    bill = Bill.objects.filter(id=bill_id).first()

    if not bill:
        logger.warning(
            "Billy sync skipped: bill not found bill_id=%s",
            bill_id,
        )

        return {
            "ok": False,
            "reason": "bill_not_found",
            "bill_id": str(bill_id),
        }

    if not bill.cufe:
        logger.info(
            "Billy sync skipped: bill has no CUFE bill_id=%s",
            bill_id,
        )

        return {
            "ok": False,
            "reason": "missing_cufe",
            "bill_id": str(bill_id),
        }

    lock = BillyLock()

    token = lock.acquire(
        bill.cufe,
        ttl=30,
    )

    if not token:
        logger.info(
            "Billy sync skipped: CUFE already processing "
            "bill_id=%s cufe=%s",
            bill.id,
            bill.cufe,
        )

        return {
            "ok": False,
            "reason": "already_processing",
            "bill_id": str(bill.id),
            "cufe": bill.cufe,
        }

    try:
        result = BillySyncService().sync_bill(bill)

        logger.info(
            "Billy sync task completed "
            "bill_id=%s task_id=%s result=%s",
            bill_id,
            self.request.id,
            result,
        )

        return result

    finally:
        lock.release(
            bill.cufe,
            token,
        )