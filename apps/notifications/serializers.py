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

from apps.notifications.models import NotificationRule


class NotificationRuleSerializer(serializers.ModelSerializer):
    permission_code = serializers.CharField(
        source="permission.code",
        allow_null=True,
        read_only=True,
    )
    role_ids = serializers.SerializerMethodField()
    role_names = serializers.SerializerMethodField()
    include_user_ids = serializers.SerializerMethodField()
    include_user_emails = serializers.SerializerMethodField()
    exclude_user_ids = serializers.SerializerMethodField()
    exclude_user_emails = serializers.SerializerMethodField()

    class Meta:
        model = NotificationRule
        fields = [
            "id",
            "event_type",
            "label",
            "description",
            "enabled",
            "send_email",
            "permission_code",
            "include_entity_creator",
            "role_ids",
            "role_names",
            "include_user_ids",
            "include_user_emails",
            "exclude_user_ids",
            "exclude_user_emails",
            "updated_at",
        ]

    def get_role_ids(self, obj):
        return list(obj.roles.values_list("id", flat=True))

    def get_role_names(self, obj):
        return list(obj.roles.values_list("name", flat=True))

    def get_include_user_ids(self, obj):
        return list(obj.include_users.values_list("id", flat=True))

    def get_include_user_emails(self, obj):
        return list(obj.include_users.values_list("email", flat=True))

    def get_exclude_user_ids(self, obj):
        return list(obj.exclude_users.values_list("id", flat=True))

    def get_exclude_user_emails(self, obj):
        return list(obj.exclude_users.values_list("email", flat=True))
