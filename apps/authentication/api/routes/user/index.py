# views
from django.urls import path
from apps.authentication.api.views.index import UserAV, UserRolesAV

urlpatterns = [
    path('', UserAV.as_view(), name='user_role'),
    path('<uuid:pk>', UserAV.as_view(), name='user_role_id'),
    path('<uuid:pk>/roles', UserRolesAV.as_view(), name='user_role_id_roles')
]