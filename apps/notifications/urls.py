from django.urls import path

from apps.notifications.views import (
    NotificationListView,
    NotificationMarkAllReadView,
    NotificationReadView,
    NotificationRuleDetailView,
    NotificationRuleListView,
    NotificationRuleOptionsView,
)


urlpatterns = [
    path(
        "",
        NotificationListView.as_view(),
        name="notification-list",
    ),
    path(
        "admin/rules/",
        NotificationRuleListView.as_view(),
        name="notification-rule-list",
    ),
    path(
        "admin/rules/options/",
        NotificationRuleOptionsView.as_view(),
        name="notification-rule-options",
    ),
    path(
        "admin/rules/<uuid:rule_id>/",
        NotificationRuleDetailView.as_view(),
        name="notification-rule-detail",
    ),
    path(
        "<uuid:notification_id>/read/",
        NotificationReadView.as_view(),
        name="notification-read",
    ),
    path(
        "mark-all-read/",
        NotificationMarkAllReadView.as_view(),
        name="notification-mark-all-read",
    ),
]
