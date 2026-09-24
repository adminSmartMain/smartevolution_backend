import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.db.models import Case, F, IntegerField, Value, When
from django.utils import timezone

from apps.bill.models import Bill
from apps.bill.services.billy import (
    BillyLock,
    BillyPollingState,
    BillyRateLimiter,
    BillySyncService,
    calculate_bill_next_check,
    filter_eligible_for_billy_polling,
    is_bill_eligible_for_billy_polling,
)
from apps.bill.services.billy.polling import apply_watchlist_exit_rule
from apps.bill.services.billy.exceptions import (
    BillyAPIError,
    BillyAuthenticationError,
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

# 404 no dispara retries Celery. Se reprograma la factura con un backoff
# progresivo para dejar de consultar agresivamente CUFEs aún no disponibles.
NOT_FOUND_BACKOFF_SECONDS = (
    15 * 60,
    30 * 60,
    60 * 60,
    3 * 60 * 60,
    6 * 60 * 60,
    12 * 60 * 60,
    24 * 60 * 60,
)


def _get_retry_countdown(retries):
    index = min(
        retries,
        len(BACKOFF_SECONDS) - 1,
    )

    return BACKOFF_SECONDS[index]


def _get_not_found_countdown(consecutive_errors):
    index = min(
        max(int(consecutive_errors or 1) - 1, 0),
        len(NOT_FOUND_BACKOFF_SECONDS) - 1,
    )
    return NOT_FOUND_BACKOFF_SECONDS[index]


def _defer_without_retry(bill_id, countdown, reason):
    """Reprograma sin llenar la cola de retries de Celery."""
    next_check = timezone.now() + timedelta(
        seconds=max(int(countdown or 1), 1) + 30
    )
    Bill.objects.filter(id=bill_id).update(
        billyEventsNextCheckAt=next_check,
    )
    logger.warning(
        "Billy request deferred bill_id=%s reason=%s retry_in=%ss next_check=%s",
        bill_id,
        reason,
        countdown,
        next_check,
    )
    return next_check


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


def _schedule_by_business_rule(bill):
    """Vuelve a la cadencia funcional preservando elegibilidad y Watchlist."""
    bill.refresh_from_db(fields=["typeBill", "onWatchlist"])

    next_check = calculate_bill_next_check(
        bill,
        timezone.now(),
    )

    Bill.objects.filter(id=bill.id).update(
        billyEventsNextCheckAt=next_check,
    )
    return next_check


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


def _schedule_after_retry_exhaustion(bill):
    """
    Al agotarse los retries técnicos, la factura vuelve a su
    frecuencia funcional normal en lugar de recibir una demora
    arbitraria.
    """
    return _schedule_by_business_rule(bill)



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
        next_check = _schedule_after_retry_exhaustion(bill)

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
def sync_bill_events(self, bill_id, queue_token=None):
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

    polling_state = BillyPollingState()

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

        polling_state.release_queue_slot(bill_id, queue_token)
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

        polling_state.release_queue_slot(bill_id, queue_token)
        return {
            "ok": False,
            "reason": "missing_cufe",
            "bill_id": str(bill_id),
        }

    # Revalidación al ejecutar: una operación pudo cancelarse después de que
    # Beat construyó su batch. Watchlist sigue siendo override manual.
    if not is_bill_eligible_for_billy_polling(bill):
        polling_state.release_queue_slot(bill_id, queue_token)
        logger.info("Billy sync skipped: bill is not eligible bill_id=%s", bill_id)
        return {
            "ok": False,
            "reason": "not_eligible",
            "bill_id": str(bill_id),
        }

    lock = BillyLock()

    token = lock.acquire(
        bill.cufe,
        ttl=30,
    )

    if not token:
        polling_state.release_queue_slot(bill_id, queue_token)
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

        # BillySyncService puede haber cambiado typeBill en base de datos.
        # Refrescamos antes de aplicar reglas de Watchlist y calcular
        # la próxima frecuencia.
        bill.refresh_from_db(
            fields=[
                "typeBill",
                "onWatchlist",
                "watchlistActivatedAt",
                "watchlistActivatedBy",
            ]
        )

        apply_watchlist_exit_rule(bill)

        changed = bool(
            result.get("events_created")
            or result.get("owner_changed")
            or result.get("type_changed")
        )

        if changed:
            polling_state.reset_unchanged(bill.id)
            unchanged_streak = 0
        else:
            unchanged_streak = polling_state.register_unchanged(bill.id)

        next_check = calculate_bill_next_check(
            bill,
            now,
            unchanged_streak=unchanged_streak,
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
    # RATE LIMIT LOCAL / BLOQUEO GLOBAL
    # =========================================================
    except BillyLocalRateLimitError as exc:
        countdown = max(int(exc.retry_after or 60), 1)
        next_check = _defer_without_retry(
            bill.id,
            countdown,
            f"local_rate_limit:{exc.scope or 'unknown'}",
        )
        return {
            "ok": False,
            "reason": "local_rate_limit",
            "scope": exc.scope,
            "bill_id": str(bill.id),
            "next_check": next_check.isoformat(),
        }

    # =========================================================
    # 429 DE BILLY: BillyClient ya activó el circuit breaker global
    # =========================================================
    except BillyRateLimitError as exc:
        try:
            countdown = int(exc.retry_after or 60)
        except (TypeError, ValueError):
            countdown = 60

        next_check = _defer_without_retry(
            bill.id,
            max(countdown, 1),
            "billy_429",
        )
        return {
            "ok": False,
            "reason": "billy_rate_limit",
            "bill_id": str(bill.id),
            "next_check": next_check.isoformat(),
        }

    # =========================================================
    # AUTH: no insistimos con el mismo token rechazado
    # =========================================================
    except BillyAuthenticationError as exc:
        next_check = _defer_without_retry(
            bill.id,
            getattr(settings, "BILLY_AUTH_RETRY_SECONDS", 60 * 60),
            "authentication",
        )
        logger.error("Billy authentication error bill_id=%s error=%s", bill.id, exc)
        return {
            "ok": False,
            "reason": "authentication_error",
            "bill_id": str(bill.id),
            "next_check": next_check.isoformat(),
        }

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
        errors = _register_polling_error(bill.id)
        countdown = _get_not_found_countdown(errors)
        next_check = _defer_without_retry(
            bill.id,
            countdown,
            "not_found",
        )

        logger.warning(
            "Billy invoice not found bill_id=%s cufe=%s "
            "consecutive_errors=%s next_check=%s",
            bill_id,
            bill.cufe,
            errors,
            next_check,
        )

        return {
            "ok": False,
            "reason": "not_found",
            "bill_id": str(bill.id),
            "cufe": bill.cufe,
            "consecutive_errors": errors,
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
        # 4xx: registramos el fallo, pero la cadencia funcional
        # de la factura se conserva. Un 401/404 de Billy no debe
        # convertir una FV de 1h en una factura de 24h ni sacarla
        # definitivamente del scheduler.
        # -------------------------
        if (
            exc.status_code
            and 400 <= exc.status_code < 500
        ):
            next_check = _schedule_by_business_rule(bill)

            logger.warning(
                "Billy client error; polling kept by business rule "
                "bill_id=%s cufe=%s status=%s next_check=%s",
                bill_id,
                bill.cufe,
                exc.status_code,
                next_check,
            )

            return {
                "ok": False,
                "reason": "client_error",
                "bill_id": str(bill.id),
                "cufe": bill.cufe,
                "status_code": exc.status_code,
                "next_check": (
                    next_check.isoformat()
                    if next_check
                    else None
                ),
            }

        # Si BillyAPIError llega sin status conocido,
        # no ocultamos el error.
        raise

    finally:
        lock.release(
            bill.cufe,
            token,
        )
        polling_state.release_queue_slot(bill_id, queue_token)


@shared_task(
    name="apps.bill.tasks.schedule_due_billy_bills",
    queue="billy",
)
def schedule_due_billy_bills():
    now = timezone.now()
    batch_size = getattr(settings, "BILLY_SCHEDULER_BATCH_SIZE", 100)

    # Beat mira el presupuesto antes de encolar. El BillyClient vuelve a
    # validarlo atómicamente justo antes de cada request HTTP; esta doble capa
    # evita tanto colas inútiles como superar el límite por concurrencia.
    budget = BillyRateLimiter().get_budget()
    if not budget.get("available"):
        logger.warning(
            "Billy scheduler paused scope=%s retry_after=%s",
            budget.get("scope"),
            budget.get("retry_after"),
        )
        return {
            "ok": True,
            "due_total": 0,
            "scheduled": 0,
            "batch_size": batch_size,
            "reason": budget.get("scope"),
            "retry_after": budget.get("retry_after", 0),
        }

    allowed_batch = min(
        batch_size,
        budget.get("minute_remaining", 0),
        budget.get("hour_remaining", 0),
    )

    if allowed_batch <= 0:
        return {
            "ok": True,
            "due_total": 0,
            "scheduled": 0,
            "batch_size": batch_size,
            "reason": "budget_exhausted",
        }

    # Nueva elegibilidad: solo facturas con al menos una operation viva
    # (status != 4). Watchlist se conserva como override explícito.
    due_queryset = filter_eligible_for_billy_polling(
        Bill.objects.filter(
            cufe__isnull=False,
            billyEventsNextCheckAt__isnull=False,
            billyEventsNextCheckAt__lte=now,
        ).exclude(cufe="")
    )

    # Prioridades existentes intactas: Watchlist > nunca intentada > resto.
    due_queryset = (
        due_queryset
        .annotate(
            schedulerPriority=Case(
                When(onWatchlist=True, then=Value(0)),
                When(billyEventsLastAttemptAt__isnull=True, then=Value(1)),
                default=Value(2),
                output_field=IntegerField(),
            )
        )
        .order_by("schedulerPriority", "billyEventsNextCheckAt")
    )

    due_total = due_queryset.count()
    candidate_ids = list(
        due_queryset.values_list("id", flat=True)[:allowed_batch]
    )

    scheduled_ids = []
    claim_until = now + timedelta(minutes=30)
    polling_state = BillyPollingState()

    for bill_id in candidate_ids:
        # Deduplicación antes del claim: una misma factura no puede quedar
        # varias veces pendiente en la cola Billy.
        queue_token = polling_state.acquire_queue_slot(bill_id)
        if not queue_token:
            continue

        claimed = Bill.objects.filter(
            id=bill_id,
            billyEventsNextCheckAt__isnull=False,
            billyEventsNextCheckAt__lte=now,
        ).update(billyEventsNextCheckAt=claim_until)

        if not claimed:
            polling_state.release_queue_slot(bill_id, queue_token)
            continue

        try:
            sync_bill_events.delay(str(bill_id), queue_token)
        except Exception:
            polling_state.release_queue_slot(bill_id, queue_token)
            Bill.objects.filter(id=bill_id).update(
                billyEventsNextCheckAt=now + timedelta(minutes=1),
            )
            logger.exception("Could not enqueue Billy task bill_id=%s", bill_id)
            continue

        scheduled_ids.append(bill_id)

    logger.info(
        "Billy scheduler completed due_total=%s scheduled=%s "
        "batch_size=%s allowed_batch=%s minute_remaining=%s hour_remaining=%s",
        due_total,
        len(scheduled_ids),
        batch_size,
        allowed_batch,
        budget.get("minute_remaining"),
        budget.get("hour_remaining"),
    )

    return {
        "ok": True,
        "due_total": due_total,
        "scheduled": len(scheduled_ids),
        "batch_size": batch_size,
        "allowed_batch": allowed_batch,
        "minute_remaining": budget.get("minute_remaining"),
        "hour_remaining": budget.get("hour_remaining"),
    }

