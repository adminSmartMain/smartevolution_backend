from apps.notifications.events import NotificationEvent
from apps.notifications.models import Notification
from apps.notifications.services.notification_service import NotificationService
from apps.notifications.services.recipient_service import NotificationRecipientService


PREOPERATION_APPROVAL_PERMISSION = "preoperations.approve"


def notify_preoperation_pending_approval(preoperation):
    """Notify active internal users who can approve a newly pending preoperation."""
    if preoperation.status != 0:
        return 0

    recipients = NotificationRecipientService.users_with_permission(
        PREOPERATION_APPROVAL_PERMISSION
    )

    entity_label = preoperation.opId or str(preoperation.id)
    entity_id = str(preoperation.id)
    notified = 0

    for recipient in recipients.iterator():
        already_notified = Notification.objects.filter(
            recipient=recipient,
            event_type=NotificationEvent.PREOPERATION_PENDING_APPROVAL,
            entity_type="preoperation",
            entity_id=entity_id,
        ).exists()

        if already_notified:
            continue

        NotificationService.create_notification(
            recipient=recipient,
            event_type=NotificationEvent.PREOPERATION_PENDING_APPROVAL,
            title="Operación pendiente de aprobación",
            message=f"La operación {entity_label} requiere aprobación.",
            entity_type="preoperation",
            entity_id=entity_id,
            entity_label=entity_label,
            metadata={
                "status": preoperation.status,
            },
        )
        notified += 1

    return notified
