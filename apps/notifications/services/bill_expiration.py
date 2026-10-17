from datetime import date, datetime, timedelta
import logging

from django.utils import timezone

from apps.notifications.events import NotificationEvent
from apps.notifications.models import Notification
from apps.notifications.services.notification_service import NotificationService
from apps.notifications.services.recipient_service import NotificationRecipientService


logger = logging.getLogger(__name__)

BILL_EXPIRING_DAYS = 7
ELIGIBLE_BILL_TYPES = {"FV", "FV-TV"}


def parse_expiration_date(value):
    """Normalize the historical Bill.expirationDate string formats to ``date``."""
    if not value:
        return None

    value = str(value).strip()
    if value.upper() == "SIN_FECHA":
        return None

    for date_format in (
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
    ):
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            continue

    logger.warning("Unsupported bill expiration date format: %s", value)
    return None


def normalize_reference_date(reference_date=None):
    value = reference_date or timezone.now().date()
    if isinstance(value, datetime):
        value = value.date()
    if not isinstance(value, date):
        raise ValueError("reference_date must be a date or datetime instance")
    return value


def is_upcoming_expiration(expiration_date, reference_date, days_before=BILL_EXPIRING_DAYS):
    """Return True only for tomorrow through ``days_before`` days ahead."""
    if expiration_date is None:
        return False
    if not isinstance(reference_date, date):
        raise ValueError("reference_date must be a date instance")
    if not isinstance(days_before, int) or days_before < 1:
        raise ValueError("days_before must be a positive integer")

    return reference_date < expiration_date <= reference_date + timedelta(days=days_before)


def is_bill_eligible_for_expiring_notification(bill):
    """Match the same bill universe used by BILL_EXPIRED."""
    if getattr(bill, "endorsed", False):
        return True

    try:
        description = bill.typeBill.description
    except Exception:
        description = None

    return description in ELIGIBLE_BILL_TYPES


def process_expiring_bill(bill, reference_date=None, days_before=BILL_EXPIRING_DAYS):
    """Create BILL_EXPIRING immediately for one bill when applicable.

    This function is intentionally idempotent per bill/recipient: it can be
    called by a realtime Bill post_save hook and by the periodic reconciliation
    task without creating duplicate notifications.
    """
    today = normalize_reference_date(reference_date)

    if not isinstance(days_before, int) or days_before < 1:
        raise ValueError("days_before must be a positive integer")

    if not is_bill_eligible_for_expiring_notification(bill):
        return {
            "status": "not_eligible",
            "notified": 0,
            "already_notified": 0,
            "skipped_without_recipient": 0,
        }

    expiration_date = parse_expiration_date(getattr(bill, "expirationDate", None))
    if expiration_date is None:
        return {
            "status": "invalid_date",
            "notified": 0,
            "already_notified": 0,
            "skipped_without_recipient": 0,
        }

    if not is_upcoming_expiration(expiration_date, today, days_before):
        return {
            "status": "outside_window",
            "notified": 0,
            "already_notified": 0,
            "skipped_without_recipient": 0,
        }

    recipients = NotificationRecipientService.recipients_for_event(
        NotificationEvent.BILL_EXPIRING,
        entity_creator=getattr(bill, "user_created_at", None),
    )

    if not recipients.exists():
        return {
            "status": "without_recipient",
            "notified": 0,
            "already_notified": 0,
            "skipped_without_recipient": 1,
        }

    days_remaining = (expiration_date - today).days
    notified = 0
    already_notified = 0

    for recipient in recipients.iterator():
        exists = Notification.objects.filter(
            recipient=recipient,
            event_type=NotificationEvent.BILL_EXPIRING,
            entity_type="bill",
            entity_id=str(bill.id),
        ).exists()

        if exists:
            already_notified += 1
            continue

        NotificationService.create_notification(
            recipient=recipient,
            event_type=NotificationEvent.BILL_EXPIRING,
            title="Factura próxima a vencer",
            message=(
                f"La factura {bill.billId} vence el "
                f"{expiration_date.isoformat()} ({days_remaining} día(s))."
            ),
            entity_type="bill",
            entity_id=bill.id,
            entity_label=bill.billId,
            metadata={
                "expiration_date": expiration_date.isoformat(),
                "days_remaining": days_remaining,
                "days_before": days_before,
            },
        )
        notified += 1

    return {
        "status": "processed",
        "notified": notified,
        "already_notified": already_notified,
        "skipped_without_recipient": 0,
    }
