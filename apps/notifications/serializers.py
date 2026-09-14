from rest_framework import serializers

from apps.notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    entity = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "event_type",
            "title",
            "message",
            "is_read",
            "created_at",
            "entity",
            "metadata",
        ]

    def get_entity(self, obj):
        return {
            "type": obj.entity_type,
            "id": obj.entity_id,
            "label": obj.entity_label,
        }