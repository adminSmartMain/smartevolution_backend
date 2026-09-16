import logging

from django.db.models import Q

from apps.authentication.models import Role, User, UserRole
from apps.notifications.models import NotificationRule


logger = logging.getLogger(__name__)


class NotificationRecipientService:
    """Resolve recipients from administrable notification rules."""

    @staticmethod
    def _eligible_users():
        return User.objects.filter(
            is_active=True,
            archived_at__isnull=True,
            client_access__isnull=True,
        )

    @staticmethod
    def recipients_for_event(event_type, entity_creator=None):
        try:
            rule = (
                NotificationRule.objects
                .select_related("permission")
                .prefetch_related("roles", "include_users", "exclude_users")
                .get(event_type=event_type)
            )
        except NotificationRule.DoesNotExist:
            logger.warning(
                "No notification recipient rule configured for event %s",
                event_type,
            )
            return User.objects.none()

        if not rule.enabled:
            return User.objects.none()

        recipient_ids = set()

        if rule.permission_id:
            role_ids = rule.permission.role_assignments.filter(
                state=True,
                role__state=True,
                role__audience=Role.AUDIENCE_INTERNAL,
            ).values_list("role_id", flat=True)

            recipient_ids.update(
                UserRole.objects.filter(
                    state=True,
                    role__state=True,
                    role__audience=Role.AUDIENCE_INTERNAL,
                    role_id__in=role_ids,
                ).values_list("user_id", flat=True)
            )

            # Superusers pass permission checks throughout the platform.
            recipient_ids.update(
                NotificationRecipientService._eligible_users()
                .filter(is_superuser=True)
                .values_list("id", flat=True)
            )

        configured_role_ids = rule.roles.filter(
            state=True,
            audience=Role.AUDIENCE_INTERNAL,
        ).values_list("id", flat=True)

        recipient_ids.update(
            UserRole.objects.filter(
                state=True,
                role__state=True,
                role__audience=Role.AUDIENCE_INTERNAL,
                role_id__in=configured_role_ids,
            ).values_list("user_id", flat=True)
        )

        recipient_ids.update(
            rule.include_users.filter(
                is_active=True,
                archived_at__isnull=True,
                client_access__isnull=True,
            ).values_list("id", flat=True)
        )

        if (
            rule.include_entity_creator
            and entity_creator is not None
            and getattr(entity_creator, "is_active", False)
            and getattr(entity_creator, "archived_at", None) is None
            and not hasattr(entity_creator, "client_access")
        ):
            recipient_ids.add(entity_creator.id)

        excluded_ids = set(
            rule.exclude_users.values_list("id", flat=True)
        )
        recipient_ids.difference_update(excluded_ids)

        if not recipient_ids:
            return User.objects.none()

        return (
            NotificationRecipientService._eligible_users()
            .filter(id__in=recipient_ids)
            .distinct()
        )
