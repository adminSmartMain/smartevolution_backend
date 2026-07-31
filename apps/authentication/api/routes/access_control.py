from django.urls import path
from apps.authentication.api.views.access_control import MeAV, ProfileAV, PermissionListAV, RoleListAV, RoleDetailAV, UserAdminAV, UserMetricsAV, UserAdminDetailAV, UserPasswordAV, UserArchiveAV, UserRestoreAV, UserOperationsAV, ClientAccessAV, ClientAccessDetailAV, ClientAccessOptionsAV, AccessAuditAV

urlpatterns = [
    path('me/',MeAV.as_view()), path('profile/',ProfileAV.as_view()), path('permissions/',PermissionListAV.as_view()),
    path('roles/',RoleListAV.as_view()), path('roles/<str:pk>/',RoleDetailAV.as_view()),
    path('users/',UserAdminAV.as_view()), path('users/metrics/',UserMetricsAV.as_view()), path('users/<str:pk>/',UserAdminDetailAV.as_view()),
    path('users/<str:pk>/password/',UserPasswordAV.as_view()),
    path('users/<str:pk>/archive/',UserArchiveAV.as_view()),
    path('users/<str:pk>/restore/',UserRestoreAV.as_view()),
    path('users/<str:pk>/operations/',UserOperationsAV.as_view()),
    path('client-access/',ClientAccessAV.as_view()), path('client-access/options/',ClientAccessOptionsAV.as_view()), path('client-access/<str:pk>/',ClientAccessDetailAV.as_view()),
    path('audit/',AccessAuditAV.as_view()),
]
