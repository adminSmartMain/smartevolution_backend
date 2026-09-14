from apps.notifications.models import Notification


class NotificationService:

    @staticmethod
    def create_notification(
        *,
        recipient,
        event_type,
        title,
        message,
        entity_type,
        entity_id,
        entity_label,
        metadata=None,
    ):
        notification = Notification.objects.create(
            recipient=recipient,
            event_type=event_type,
            title=title,
            message=message,
            entity_type=entity_type,
            entity_id=str(entity_id),
            entity_label=entity_label,
            metadata=metadata or {},
        )

        return notification