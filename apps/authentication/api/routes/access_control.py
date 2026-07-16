from django.urls import path
from apps.authentication.api.views.access_control import MeAV, ProfileAV, PermissionListAV, RoleListAV, RoleDetailAV, UserAdminAV, UserAdminDetailAV, ClientAccessAV, ClientAccessDetailAV, ClientAccessOptionsAV, AccessAuditAV

urlpatterns = [
    path('me/',MeAV.as_view()), path('profile/',ProfileAV.as_view()), path('permissions/',PermissionListAV.as_view()),
    path('roles/',RoleListAV.as_view()), path('roles/<str:pk>/',RoleDetailAV.as_view()),
    path('users/',UserAdminAV.as_view()), path('users/<str:pk>/',UserAdminDetailAV.as_view()),
    path('client-access/',ClientAccessAV.as_view()), path('client-access/options/',ClientAccessOptionsAV.as_view()), path('client-access/<str:pk>/',ClientAccessDetailAV.as_view()),
    path('audit/',AccessAuditAV.as_view()),
]
