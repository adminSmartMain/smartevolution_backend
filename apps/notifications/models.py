import uuid

from django.conf import settings
from django.db import models


class Notification(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    event_type = models.CharField(max_length=100)

    title = models.CharField(max_length=255)

    message = models.TextField()

    entity_type = models.CharField(max_length=100)

    entity_id = models.CharField(max_length=255)

    entity_label = models.CharField(max_length=255)

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    is_read = models.BooleanField(
        default=False,
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=["recipient", "is_read", "created_at"],
                name="notif_user_read_date_idx",
            ),
        ]

    def __str__(self):
        return f"{self.event_type} -> {self.recipient}"