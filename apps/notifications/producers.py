from apps.notifications.events import NotificationEvent
from apps.operation.models import BuyOrder
from apps.notifications.models import Notification
from apps.notifications.services.notification_service import NotificationService
from apps.notifications.services.recipient_service import NotificationRecipientService


PREOPERATION_APPROVAL_PERMISSION = "preoperations.approve"
ELECTRONIC_SIGNATURE_PERMISSION = "operations.create"


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


def notify_electronic_signature_pending(preoperation):
    """Notify users when an operation/investor still requires signature management."""
    if preoperation.status != 0:
        return 0

    has_buy_order = BuyOrder.objects.filter(
        operation__opId=preoperation.opId,
        operation__investor_id=preoperation.investor_id,
    ).exists()
    if has_buy_order:
        return 0

    recipients = NotificationRecipientService.users_with_permission(
        ELECTRONIC_SIGNATURE_PERMISSION
    )

    entity_id = f"{preoperation.opId}:{preoperation.investor_id}"
    entity_label = f"OP-{preoperation.opId}"
    notified = 0

    for recipient in recipients.iterator():
        already_notified = Notification.objects.filter(
            recipient=recipient,
            event_type=NotificationEvent.ELECTRONIC_SIGNATURE_PENDING,
            entity_type="electronic_signature",
            entity_id=entity_id,
        ).exists()

        if already_notified:
            continue

        NotificationService.create_notification(
            recipient=recipient,
            event_type=NotificationEvent.ELECTRONIC_SIGNATURE_PENDING,
            title="Firma electrónica pendiente",
            message=f"La operación {entity_label} requiere gestionar su firma electrónica.",
            entity_type="electronic_signature",
            entity_id=entity_id,
            entity_label=entity_label,
            metadata={
                "op_id": str(preoperation.opId),
                "investor_id": str(preoperation.investor_id),
            },
        )
        notified += 1

    return notified
