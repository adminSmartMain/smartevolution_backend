import logging

from django.db.models import Q

from apps.authentication.models import Permission, Role, User, UserRole
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
    def preview_draft(
        *,
        enabled=True,
        permission_code=None,
        role_ids=None,
        include_user_ids=None,
        exclude_user_ids=None,
        include_entity_creator=False,
    ):
        """Resolve a draft rule without persisting it.

        This is used by the administration UI to explain who matches the
        configured criteria. The entity creator cannot be resolved until a
        concrete event occurs, so it is reported separately as a runtime
        inclusion.
        """
        role_ids = role_ids or []
        include_user_ids = include_user_ids or []
        exclude_user_ids = exclude_user_ids or []

        reason_map = {}

        def add_reason(user_id, reason_type, label):
            reasons = reason_map.setdefault(str(user_id), [])
            reason = {"type": reason_type, "label": label}
            if reason not in reasons:
                reasons.append(reason)

        eligible_users = NotificationRecipientService._eligible_users()

        if permission_code:
            permission = Permission.objects.filter(
                code=permission_code,
                state=True,
            ).first()
            if permission is None:
                raise ValueError("El permiso seleccionado no existe o está inactivo.")

            permission_role_ids = permission.role_assignments.filter(
                state=True,
                role__state=True,
                role__audience=Role.AUDIENCE_INTERNAL,
            ).values_list("role_id", flat=True)

            permission_user_ids = UserRole.objects.filter(
                state=True,
                role__state=True,
                role__audience=Role.AUDIENCE_INTERNAL,
                role_id__in=permission_role_ids,
            ).values_list("user_id", flat=True)

            for user_id in permission_user_ids:
                add_reason(
                    user_id,
                    "permission",
                    f"Permiso base: {permission_code}",
                )

            for user_id in eligible_users.filter(
                is_superuser=True
            ).values_list("id", flat=True):
                add_reason(
                    user_id,
                    "permission",
                    f"Permiso base: {permission_code} (superusuario)",
                )

        configured_roles = list(
            Role.objects.filter(
                id__in=role_ids,
                state=True,
                audience=Role.AUDIENCE_INTERNAL,
            ).values("id", "name", "code")
        )

        for role in configured_roles:
            user_ids = UserRole.objects.filter(
                state=True,
                role_id=role["id"],
                role__state=True,
                role__audience=Role.AUDIENCE_INTERNAL,
            ).values_list("user_id", flat=True)
            role_label = role["name"] or role["code"] or str(role["id"])
            for user_id in user_ids:
                add_reason(
                    user_id,
                    "role",
                    f"Rol adicional: {role_label}",
                )

        for user in eligible_users.filter(id__in=include_user_ids):
            add_reason(
                user.id,
                "user",
                "Usuario adicional",
            )

        excluded_ids = {str(value) for value in exclude_user_ids}
        matched_ids = set(reason_map.keys())
        recipient_ids = matched_ids.difference(excluded_ids)

        def serialize_user(user, reasons):
            return {
                "id": user.id,
                "email": user.email,
                "name": (
                    f"{user.first_name or ''} {user.last_name or ''}".strip()
                    or user.email
                ),
                "is_superuser": user.is_superuser,
                "reasons": reasons,
            }

        recipients = []
        for user in eligible_users.filter(id__in=recipient_ids).order_by(
            "first_name", "last_name", "email"
        ):
            recipients.append(
                serialize_user(user, reason_map.get(str(user.id), []))
            )

        excluded = []
        for user in eligible_users.filter(id__in=excluded_ids).order_by(
            "first_name", "last_name", "email"
        ):
            reasons = list(reason_map.get(str(user.id), []))
            reasons.append({
                "type": "exclusion",
                "label": "Exclusión manual",
            })
            excluded.append(serialize_user(user, reasons))

        return {
            "rule_enabled": bool(enabled),
            "recipients": recipients,
            "excluded": excluded,
            "matched_count": len(recipients),
            "effective_count": len(recipients) if enabled else 0,
            "excluded_count": len(excluded),
            "entity_creator_runtime": bool(include_entity_creator),
        }

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
