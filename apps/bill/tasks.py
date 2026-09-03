import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.db.models import F
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
    BillyNotFoundError,
    BillyRateLimitError,
    BillyTimeoutError,
)


logger = logging.getLogger(__name__)


MAX_RETRIES = 4

BACKOFF_SECONDS = (
    15 * 60,      # 15 minutos
    30 * 60,      # 30 minutos
    60 * 60,      # 1 hora
    2 * 60 * 60,  # 2 horas
)


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

    return (
        Bill.objects.filter(id=bill_id)
        .values_list(
            "billyEventsConsecutiveErrors",
            flat=True,
        )
        .first()
    )


def _schedule_not_found_retry(bill_id):
    """
    Billy no conoce actualmente el CUFE.

    No hacemos retry técnico inmediato.
    Lo volvemos a consultar dentro de 24 horas.
    """
    next_check = timezone.now() + timedelta(hours=24)

    Bill.objects.filter(id=bill_id).update(
        billyEventsNextCheckAt=next_check,
    )

    return next_check


def _disable_polling(bill_id):
    """
    Desactiva el polling automático para una factura.

    Se utiliza cuando Billy responde con un error
    de cliente 4xx que no tiene sentido reintentar
    automáticamente.
    """
    Bill.objects.filter(id=bill_id).update(
        billyEventsNextCheckAt=None,
    )


def _reserve_polling_until_retry(bill_id, countdown):
    """
    Evita que Beat vuelva a encolar una factura mientras Celery
    ya tiene un retry programado.
    """
    next_check = timezone.now() + timedelta(
        seconds=max(int(countdown or 0), 0) + 60
    )

    Bill.objects.filter(id=bill_id).update(
        billyEventsNextCheckAt=next_check,
    )

    return next_check


def _schedule_after_retry_exhaustion(bill_id):
    """
    Cuando se agotan los retries técnicos, devuelve la factura al
    polling futuro sin propagar indefinidamente la excepción.
    """
    next_check = timezone.now() + timedelta(hours=6)

    Bill.objects.filter(id=bill_id).update(
        billyEventsNextCheckAt=next_check,
    )

    return next_check


def _retry_or_defer(
    task,
    bill,
    exc,
    countdown,
    errors,
    log_label,
):
    """
    Programa un retry técnico y reserva NextCheckAt para que Beat no
    duplique el trabajo. Si Celery agotó los retries, posterga el
    siguiente polling y termina la tarea de forma controlada.
    """
    if task.request.retries >= MAX_RETRIES:
        next_check = _schedule_after_retry_exhaustion(bill.id)

        logger.error(
            "%s retries exhausted bill_id=%s error=%s "
            "consecutive_errors=%s next_check=%s",
            log_label,
            bill.id,
            type(exc).__name__,
            errors,
            next_check,
        )

        return {
            "ok": False,
            "reason": "retries_exhausted",
            "bill_id": str(bill.id),
            "cufe": bill.cufe,
            "error": type(exc).__name__,
            "next_check": next_check.isoformat(),
        }

    next_check = _reserve_polling_until_retry(
        bill.id,
        countdown,
    )

    logger.warning(
        "%s retry scheduled bill_id=%s error=%s "
        "retry_in=%ss attempt=%s consecutive_errors=%s "
        "next_check=%s",
        log_label,
        bill.id,
        type(exc).__name__,
        countdown,
        task.request.retries + 1,
        errors,
        next_check,
    )

    raise task.retry(
        exc=exc,
        countdown=countdown,
        max_retries=MAX_RETRIES,
    )


@shared_task(
    bind=True,
    name="apps.bill.tasks.sync_bill_events",
    queue="billy",
)
def sync_bill_events(self, bill_id):
    """
    Sincroniza una factura local contra Billy.

    La tarea:
    - busca la factura
    - valida CUFE
    - adquiere lock Redis
    - registra el intento
    - delega la sincronización a BillySyncService
    - registra éxito/error
    - calcula el próximo chequeo
    - libera siempre el lock
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

    # A partir de aquí sí consideramos que hubo
    # un intento real de sincronización.
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
            "bill_id=%s task_id=%s "
            "next_check=%s result=%s",
            bill_id,
            self.request.id,
            next_check,
            result,
        )

        return result

    # =========================================================
    # RATE LIMIT LOCAL
    # =========================================================
    except BillyLocalRateLimitError as exc:
        errors = _register_polling_error(bill.id)

        countdown = max(
            int(exc.retry_after or 1),
            1,
        )

        return _retry_or_defer(
            self,
            bill,
            exc,
            countdown,
            errors,
            "Billy local rate limit",
        )

    # =========================================================
    # RATE LIMIT DE BILLY
    # =========================================================
    except BillyRateLimitError as exc:
        errors = _register_polling_error(bill.id)

        try:
            countdown = int(exc.retry_after or 60)
        except (TypeError, ValueError):
            countdown = 60

        countdown = max(
            countdown,
            1,
        )

        return _retry_or_defer(
            self,
            bill,
            exc,
            countdown,
            errors,
            "Billy API rate limit",
        )

    # =========================================================
    # TIMEOUT / RED
    # =========================================================
    except (
        BillyTimeoutError,
        BillyConnectionError,
    ) as exc:
        errors = _register_polling_error(bill.id)

        countdown = _get_retry_countdown(
            self.request.retries
        )

        return _retry_or_defer(
            self,
            bill,
            exc,
            countdown,
            errors,
            "Temporary Billy error",
        )

    # =========================================================
    # 404 - CUFE NO ENCONTRADO EN BILLY
    # =========================================================
    except BillyNotFoundError:
        next_check = _schedule_not_found_retry(
            bill.id
        )

        logger.warning(
            "Billy invoice not found "
            "bill_id=%s cufe=%s next_check=%s",
            bill_id,
            bill.cufe,
            next_check,
        )

        return {
            "ok": False,
            "reason": "not_found",
            "bill_id": str(bill.id),
            "cufe": bill.cufe,
            "next_check": next_check.isoformat(),
        }

    # =========================================================
    # OTROS ERRORES HTTP DE BILLY
    # =========================================================
    except BillyAPIError as exc:
        # -------------------------
        # 5xx: problema temporal
        # -------------------------
        if (
            exc.status_code
            and exc.status_code >= 500
        ):
            errors = _register_polling_error(
                bill.id
            )

            countdown = _get_retry_countdown(
                self.request.retries
            )

            return _retry_or_defer(
                self,
                bill,
                exc,
                countdown,
                errors,
                "Billy server error",
            )

        # -------------------------
        # 4xx: problema de datos /
        # request, no tiene sentido
        # reintentarlo cada minuto.
        # -------------------------
        if (
            exc.status_code
            and 400 <= exc.status_code < 500
        ):
            _disable_polling(
                bill.id
            )

            logger.warning(
                "Billy client error disabling polling "
                "bill_id=%s cufe=%s status=%s",
                bill_id,
                bill.cufe,
                exc.status_code,
            )

            return {
                "ok": False,
                "reason": "client_error",
                "bill_id": str(bill.id),
                "cufe": bill.cufe,
                "status_code": exc.status_code,
            }

        # Si BillyAPIError llega sin status conocido,
        # no ocultamos el error.
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

    due_queryset = (
        Bill.objects.filter(
            cufe__isnull=False,
            billyEventsNextCheckAt__isnull=False,
            billyEventsNextCheckAt__lte=now,
        )
        .exclude(cufe="")
        .order_by("billyEventsNextCheckAt")
    )

    due_total = due_queryset.count()

    candidate_ids = list(
        due_queryset.values_list(
            "id",
            flat=True,
        )[:batch_size]
    )

    scheduled_ids = []

    claim_until = now + timedelta(minutes=10)

    for bill_id in candidate_ids:
        claimed = Bill.objects.filter(
            id=bill_id,
            billyEventsNextCheckAt__isnull=False,
            billyEventsNextCheckAt__lte=now,
        ).update(
            billyEventsNextCheckAt=claim_until,
        )

        if not claimed:
            continue

        sync_bill_events.delay(
            str(bill_id)
        )

        scheduled_ids.append(
            bill_id
        )

    logger.info(
        "Billy scheduler completed "
        "due_total=%s scheduled=%s batch_size=%s",
        due_total,
        len(scheduled_ids),
        batch_size,
    )

    return {
        "ok": True,
        "due_total": due_total,
        "scheduled": len(scheduled_ids),
        "batch_size": batch_size,
    }