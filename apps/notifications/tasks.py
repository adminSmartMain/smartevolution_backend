import logging
from datetime import date, datetime

from celery import shared_task
from django.db.models import Q
from django.utils import timezone

from apps.bill.models import Bill
from apps.notifications.events import NotificationEvent
from apps.notifications.models import Notification
from apps.notifications.services.notification_service import NotificationService


logger = logging.getLogger(__name__)


def parse_expiration_date(value):
    """
    Convierte los distintos formatos históricos de expirationDate a date.

    Valores conocidos:
    - 2026-10-01
    - 2024-08-16 00:00:00
    - 2024-03-21T00:00:00
    - SIN_FECHA
    """

    if not value:
        return None

    value = str(value).strip()

    if value.upper() == "SIN_FECHA":
        return None

    formats = (
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
    )

    for date_format in formats:
        try:
            return datetime.strptime(
                value,
                date_format,
            ).date()
        except ValueError:
            continue

    logger.warning(
        "Unsupported bill expiration date format: %s",
        value,
    )

    return None


def process_expired_bills(reference_date=None):
    """
    Genera BILL_EXPIRED para facturas elegibles que vencen
    exactamente en reference_date.

    Reglas iniciales:
    - tipo FV
    - tipo FV-TV
    - o estado Billy ENDOSADA

    No genera backlog histórico:
    una factura solo se procesa el día exacto de su vencimiento.

    reference_date existe para permitir pruebas controladas.
    En ejecución normal se utiliza la fecha actual.
    """

    today = reference_date or timezone.now().date()

    if isinstance(today, datetime):
        today = today.date()

    if not isinstance(today, date):
        raise ValueError(
            "reference_date must be a date or datetime instance"
        )

    bills = (
    Bill.objects
    .filter(
        Q(typeBill__description__in=["FV", "FV-TV"])
        | Q(endorsed=True)
    )
    .exclude(expirationDate__isnull=True)
    .exclude(expirationDate="")
    .select_related("user_created_at", "typeBill")
)

    notified = 0
    already_notified = 0
    skipped_invalid_date = 0
    skipped_without_recipient = 0

    for bill in bills.iterator():
        expiration_date = parse_expiration_date(
            bill.expirationDate
        )

        if expiration_date is None:
            skipped_invalid_date += 1
            continue

        # No reconstruimos notificaciones históricas.
        # El evento ocurre únicamente el día del vencimiento.
        if expiration_date != today:
            continue

        recipient = bill.user_created_at

        if recipient is None:
            skipped_without_recipient += 1
            continue

        notification_exists = Notification.objects.filter(
            recipient=recipient,
            event_type=NotificationEvent.BILL_EXPIRED,
            entity_type="bill",
            entity_id=str(bill.id),
        ).exists()

        if notification_exists:
            already_notified += 1
            continue

        NotificationService.create_notification(
            recipient=recipient,
            event_type=NotificationEvent.BILL_EXPIRED,
            title="Factura vencida",
            message=(
                f"La factura {bill.billId} "
                "alcanzó su fecha de vencimiento."
            ),
            entity_type="bill",
            entity_id=bill.id,
            entity_label=bill.billId,
            metadata={
                "expiration_date": expiration_date.isoformat(),
            },
        )

        notified += 1

    result = {
        "reference_date": today.isoformat(),
        "notified": notified,
        "already_notified": already_notified,
        "skipped_invalid_date": skipped_invalid_date,
        "skipped_without_recipient": skipped_without_recipient,
    }

    logger.info(
        "Expired bill notifications completed: %s",
        result,
    )

    return result


@shared_task(
    name="apps.notifications.tasks.notify_expired_bills",
)
def notify_expired_bills():
    """
    Tarea Celery ejecutada con la fecha real del sistema.
    """
    return process_expired_bills()