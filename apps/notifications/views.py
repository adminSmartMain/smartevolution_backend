from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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