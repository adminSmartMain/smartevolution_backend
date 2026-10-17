import logging

from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.bill.models import Bill
from apps.notifications.services.bill_expiration import process_expiring_bill


logger = logging.getLogger(__name__)
_RELEVANT_FIELDS = (
    "typeBill_id",
    "expirationDate",
    "endorsed",
    "user_created_at_id",
)


def _bill_expiring_state(bill):
    return tuple(getattr(bill, field, None) for field in _RELEVANT_FIELDS)


@receiver(pre_save, sender=Bill, dispatch_uid="notifications.bill_expiring.pre_save")
def capture_bill_expiring_previous_state(sender, instance, **kwargs):
    """Remember only fields that can change BILL_EXPIRING eligibility."""
    if instance._state.adding or not instance.pk:
        instance._notification_expiring_previous_state = None
        return

    previous = (
        sender.objects
        .filter(pk=instance.pk)
        .values_list(*_RELEVANT_FIELDS)
        .first()
    )
    instance._notification_expiring_previous_state = previous


@receiver(post_save, sender=Bill, dispatch_uid="notifications.bill_expiring.post_save")
def notify_when_bill_enters_expiring_window(sender, instance, created, **kwargs):
    """Evaluate BILL_EXPIRING immediately after relevant Bill changes.

    Creation always evaluates. Updates only evaluate when type, expiration date,
    endorsed state or creator changed, avoiding work on Billy/status-only saves.
    The evaluator is idempotent per bill/recipient.
    """
    previous = getattr(instance, "_notification_expiring_previous_state", None)
    current = _bill_expiring_state(instance)

    if not created and previous == current:
        return

    def evaluate_after_commit():
        try:
            result = process_expiring_bill(instance)
            if result.get("notified"):
                logger.info(
                    "Realtime BILL_EXPIRING created bill=%s result=%s",
                    instance.pk,
                    result,
                )
        except Exception:
            # Notification failures must never make Bill creation/update fail.
            logger.exception(
                "Realtime BILL_EXPIRING evaluation failed for bill=%s",
                instance.pk,
            )

    transaction.on_commit(evaluate_after_commit)
