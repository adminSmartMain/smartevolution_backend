from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.notifications"

    def ready(self):
        # Register realtime notification hooks only after Django loads apps.
        from apps.notifications import signals  # noqa: F401
