import logging
from django.db.models import F
from django.utils import timezone
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from apps.bill.models import Bill
from apps.bill.services.billy import (
    BillyLock,
    BillySyncService,
    calculate_next_check,
)

from apps.bill.services.billy.exceptions import (
    BillyAPIError,
    BillyConnectionError,
    BillyLocalRateLimitError,
    BillyRateLimitError,
    BillyTimeoutError,
)


MAX_RETRIES = 4

BACKOFF_SECONDS = (
    15 * 60,      # 15 minutos
    30 * 60,      # 30 minutos
    60 * 60,      # 1 hora
    2 * 60 * 60,  # 2 horas
)
logger = logging.getLogger(__name__)




def _get_retry_countdown(retries):
    index = min(
        retries,
        len(BACKOFF_SECONDS) - 1,
    )

    return BACKOFF_SECONDS[index]

def _register_polling_error(bill_id):
    Bill.objects.filter(id=bill_id).update(
        billyEventsConsecutiveErrors=F(
            "billyEventsConsecutiveErrors"
        ) + 1
    )

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
        Bill.objects.filter(id=bill.id).update(
    billyEventsLastAttemptAt=timezone.now(),
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
        
    Bill.objects.filter(id=bill.id).update(
        billyEventsLastAttemptAt=timezone.now(),
    )

    try:
        result = BillySyncService().sync_bill(bill)

        now = timezone.now()

        next_check = calculate_next_check(
            bill.typeBill_id,
            now,
        )

        Bill.objects.filter(id=bill.id).update(
            billyEventsLastSuccessAt=now,
            billyEventsConsecutiveErrors=0,
            billyEventsNextCheckAt=next_check,
        )
        logger.info(
            "Billy sync task completed "
            "bill_id=%s task_id=%s result=%s",
            bill_id,
            self.request.id,
            result,
        )

        return result

    except BillyLocalRateLimitError as exc:
        _register_polling_error(bill.id)
        countdown = max(
            int(exc.retry_after or 1),
            1,
        )

        logger.warning(
            "Billy local rate limit reached "
            "bill_id=%s retry_in=%ss attempt=%s",
            bill_id,
            countdown,
            self.request.retries + 1,
        )

        raise self.retry(
            exc=exc,
            countdown=countdown,
            max_retries=MAX_RETRIES,
        )

    except BillyRateLimitError as exc:
        _register_polling_error(bill.id)
        try:
            countdown = int(exc.retry_after or 60)
        except (TypeError, ValueError):
            countdown = 60

        countdown = max(countdown, 1)

        logger.warning(
            "Billy API rate limit reached "
            "bill_id=%s retry_in=%ss attempt=%s",
            bill_id,
            countdown,
            self.request.retries + 1,
        )

        raise self.retry(
            exc=exc,
            countdown=countdown,
            max_retries=MAX_RETRIES,
        )

    except (
        BillyTimeoutError,
        BillyConnectionError,
    ) as exc:
        _register_polling_error(bill.id)
        countdown = _get_retry_countdown(
            self.request.retries
        )

        logger.warning(
            "Temporary Billy error "
            "bill_id=%s error=%s "
            "retry_in=%ss attempt=%s",
            bill_id,
            type(exc).__name__,
            countdown,
            self.request.retries + 1,
        )

        raise self.retry(
            exc=exc,
            countdown=countdown,
            max_retries=MAX_RETRIES,
        )

    except BillyAPIError as exc:
        if exc.status_code and exc.status_code >= 500:
            _register_polling_error(bill.id)
            countdown = _get_retry_countdown(
                self.request.retries
            )

            logger.warning(
                "Billy server error "
                "bill_id=%s status=%s "
                "retry_in=%ss attempt=%s",
                bill_id,
                exc.status_code,
                countdown,
                self.request.retries + 1,
            )

            raise self.retry(
                exc=exc,
                countdown=countdown,
                max_retries=MAX_RETRIES,
            )

        raise

    finally:
        lock.release(
            bill.cufe,
            token,
        )
@shared_task(
name="apps.bill.tasks.schedule_due_billy_bills",
queue="billy",
)
def schedule_due_billy_bills():
    now = timezone.now()

    batch_size = getattr(
        settings,
        "BILLY_SCHEDULER_BATCH_SIZE",
        100,
    )

    due_bills = list(
        Bill.objects.filter(
            cufe__isnull=False,
            billyEventsNextCheckAt__isnull=False,
            billyEventsNextCheckAt__lte=now,
        )
        .exclude(cufe="")
        .order_by("billyEventsNextCheckAt")
        .values_list("id", flat=True)[:batch_size]
    )

    for bill_id in due_bills:
        sync_bill_events.delay(str(bill_id))

    logger.info(
        "Billy scheduler completed due=%s batch_size=%s",
        len(due_bills),
        batch_size,
    )

    return {
        "ok": True,
        "scheduled": len(due_bills),
        "batch_size": batch_size,
    } 
        
