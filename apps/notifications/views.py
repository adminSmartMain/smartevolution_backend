from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.access import permission_required
from apps.authentication.models import AccessAudit, Permission, Role, User
from apps.base.utils.index import gen_uuid
from apps.notifications.models import NotificationRule
from apps.notifications.serializers import NotificationRuleSerializer
from apps.notifications.services.recipient_service import NotificationRecipientService

from apps.notifications.models import Notification
from apps.notifications.pagination import NotificationPagination
from apps.notifications.serializers import NotificationSerializer


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(
            recipient=request.user
        )

        is_read = request.query_params.get("is_read")

        if is_read == "true":
            notifications = notifications.filter(is_read=True)
        elif is_read == "false":
            notifications = notifications.filter(is_read=False)

        unread_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).count()

        paginator = NotificationPagination()
        page = paginator.paginate_queryset(
            notifications,
            request,
        )

        serializer = NotificationSerializer(
            page,
            many=True,
        )

        return paginator.get_paginated_response(
            serializer.data,
            unread_count,
        )


class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, notification_id):
        try:
            notification = Notification.objects.get(
                id=notification_id,
                recipient=request.user,
            )
        except Notification.DoesNotExist:
            return Response(
                {"detail": "Notification not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(
                update_fields=[
                    "is_read",
                    "read_at",
                ]
            )

        return Response({
            "id": notification.id,
            "is_read": notification.is_read,
        })


class NotificationMarkAllReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        now = timezone.now()

        notifications = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        )

        updated = notifications.update(
            is_read=True,
            read_at=now,
        )

        return Response({
            "updated": updated,
            "unread_count": 0,
        })


class NotificationRuleListView(APIView):
    permission_classes = [IsAuthenticated]

    @permission_required("security.access")
    def get(self, request):
        rules = (
            NotificationRule.objects
            .select_related("permission")
            .prefetch_related("roles", "include_users", "exclude_users")
            .all()
        )
        return Response({
            "error": False,
            "data": NotificationRuleSerializer(rules, many=True).data,
        })


class NotificationRuleOptionsView(APIView):
    permission_classes = [IsAuthenticated]

    @permission_required("security.access")
    def get(self, request):
        roles = Role.objects.filter(
            state=True,
            audience=Role.AUDIENCE_INTERNAL,
        ).order_by("name")

        users = User.objects.filter(
            is_active=True,
            archived_at__isnull=True,
            client_access__isnull=True,
        ).order_by("email")

        permissions = Permission.objects.filter(
            state=True,
        ).order_by("module", "action")

        return Response({
            "error": False,
            "data": {
                "roles": [
                    {
                        "id": role.id,
                        "code": role.code,
                        "name": role.name,
                    }
                    for role in roles
                ],
                "users": [
                    {
                        "id": user.id,
                        "email": user.email,
                        "name": (
                            f"{user.first_name or ''} {user.last_name or ''}".strip()
                            or user.email
                        ),
                    }
                    for user in users
                ],
                "permissions": [
                    {
                        "code": permission.code,
                        "name": permission.name,
                        "module": permission.module,
                    }
                    for permission in permissions
                ],
            },
        })


class NotificationRulePreviewView(APIView):
    permission_classes = [IsAuthenticated]

    @permission_required("security.access")
    def post(self, request):
        data = request.data

        list_fields = (
            "role_ids",
            "include_user_ids",
            "exclude_user_ids",
        )
        for field in list_fields:
            value = data.get(field, [])
            if value is not None and not isinstance(value, list):
                return Response(
                    {
                        "error": True,
                        "message": f"{field} debe ser una lista.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            preview = NotificationRecipientService.preview_draft(
                enabled=data.get("enabled", True),
                permission_code=data.get("permission_code"),
                role_ids=data.get("role_ids") or [],
                include_user_ids=data.get("include_user_ids") or [],
                exclude_user_ids=data.get("exclude_user_ids") or [],
                include_entity_creator=data.get("include_entity_creator", False),
            )
        except ValueError as exc:
            return Response(
                {"error": True, "message": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({
            "error": False,
            "data": preview,
        })


class NotificationRuleDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @permission_required("security.access")
    def patch(self, request, rule_id):
        try:
            rule = NotificationRule.objects.get(id=rule_id)
        except NotificationRule.DoesNotExist:
            return Response(
                {"error": True, "message": "Regla de notificación no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        data = request.data

        if "enabled" in data:
            rule.enabled = bool(data["enabled"])

        if "include_entity_creator" in data:
            rule.include_entity_creator = bool(data["include_entity_creator"])

        if "permission_code" in data:
            permission_code = data.get("permission_code")
            if permission_code:
                try:
                    rule.permission = Permission.objects.get(
                        code=permission_code,
                        state=True,
                    )
                except Permission.DoesNotExist:
                    return Response(
                        {"error": True, "message": "El permiso seleccionado no existe."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                rule.permission = None

        rule.save()

        if "role_ids" in data:
            roles = Role.objects.filter(
                id__in=data.get("role_ids") or [],
                state=True,
                audience=Role.AUDIENCE_INTERNAL,
            )
            rule.roles.set(roles)

        if "include_user_ids" in data:
            users = User.objects.filter(
                id__in=data.get("include_user_ids") or [],
                is_active=True,
                archived_at__isnull=True,
                client_access__isnull=True,
            )
            rule.include_users.set(users)

        if "exclude_user_ids" in data:
            users = User.objects.filter(
                id__in=data.get("exclude_user_ids") or [],
                client_access__isnull=True,
            )
            rule.exclude_users.set(users)

        AccessAudit.objects.create(
            id=gen_uuid(),
            actor=request.user,
            action="NOTIFICATION_RULE_UPDATED",
            target_type="notification_rule",
            target_id=str(rule.id),
            details={
                "event_type": rule.event_type,
                "enabled": rule.enabled,
                "permission_code": rule.permission.code if rule.permission else None,
                "include_entity_creator": rule.include_entity_creator,
                "role_ids": list(rule.roles.values_list("id", flat=True)),
                "include_user_ids": list(rule.include_users.values_list("id", flat=True)),
                "exclude_user_ids": list(rule.exclude_users.values_list("id", flat=True)),
            },
            ip_address=request.META.get("REMOTE_ADDR"),
        )

        rule = (
            NotificationRule.objects
            .select_related("permission")
            .prefetch_related("roles", "include_users", "exclude_users")
            .get(id=rule.id)
        )

        return Response({
            "error": False,
            "data": NotificationRuleSerializer(rule).data,
        })
