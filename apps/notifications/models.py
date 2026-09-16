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

class NotificationRule(models.Model):
    """Administrable recipient routing for one notification event."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    event_type = models.CharField(
        max_length=100,
        unique=True,
    )

    label = models.CharField(
        max_length=160,
    )

    description = models.TextField(
        blank=True,
    )

    enabled = models.BooleanField(
        default=True,
    )

    permission = models.ForeignKey(
        "authentication.Permission",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="notification_rules",
    )

    include_entity_creator = models.BooleanField(
        default=False,
    )

    roles = models.ManyToManyField(
        "authentication.Role",
        blank=True,
        related_name="notification_rules",
    )

    include_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="notification_rule_inclusions",
    )

    exclude_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="notification_rule_exclusions",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["event_type"]

    def __str__(self):
        return f"{self.event_type} notification rule"
