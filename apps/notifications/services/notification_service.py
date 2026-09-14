from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction

from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer


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

        transaction.on_commit(
            lambda: NotificationService._publish_created(
                notification
            )
        )

        return notification

    @staticmethod
    def _publish_created(notification):
        channel_layer = get_channel_layer()

        if channel_layer is None:
            return

        group_name = (
            f"user_notifications_{notification.recipient_id}"
        )

        data = NotificationSerializer(notification).data

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "notification.created",
                "data": data,
            },
        )