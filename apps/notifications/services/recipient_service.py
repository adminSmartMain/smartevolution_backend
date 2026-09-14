import os

from django.db.models import Q

from apps.authentication.models import Role, RolePermission, User, UserRole


class NotificationRecipientService:
    """Resolve notification recipients using the platform RBAC model."""

    @staticmethod
    def users_with_permission(permission_code):
        test_recipient_email = os.getenv("NOTIFICATION_TEST_RECIPIENT_EMAIL", "").strip()

        if test_recipient_email:
            return User.objects.filter(
                email__iexact=test_recipient_email,
                is_active=True,
                archived_at__isnull=True,
                client_access__isnull=True,
            )

        role_ids = RolePermission.objects.filter(
            state=True,
            role__state=True,
            role__audience=Role.AUDIENCE_INTERNAL,
            permission__state=True,
            permission__code=permission_code,
        ).values_list("role_id", flat=True)

        user_ids = UserRole.objects.filter(
            state=True,
            role__state=True,
            role__audience=Role.AUDIENCE_INTERNAL,
            role_id__in=role_ids,
        ).values_list("user_id", flat=True)

        return (
            User.objects.filter(
                is_active=True,
                archived_at__isnull=True,
                client_access__isnull=True,
            )
            .filter(
                Q(is_superuser=True)
                | Q(id__in=user_ids)
            )
            .distinct()
        )
