from django.contrib import admin

from apps.notifications.models import Notification, NotificationRule


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("event_type", "recipient", "entity_label", "is_read", "created_at")
    list_filter = ("event_type", "is_read")
    search_fields = ("recipient__email", "entity_label", "title")


@admin.register(NotificationRule)
class NotificationRuleAdmin(admin.ModelAdmin):
    list_display = ("event_type", "enabled", "send_email", "permission", "include_entity_creator", "updated_at")
    list_filter = ("enabled", "include_entity_creator")
    search_fields = ("event_type", "label")
    filter_horizontal = ("roles", "include_users", "exclude_users")
