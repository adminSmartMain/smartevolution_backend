# views
from django.urls import path
from apps.client.api.views.index import ClientAV, ClientByTermAV
from apps.client.api.views.client.index import ClientRoleViewSet, ClientRoleAssignmentViewSet


# Assignments
client_role_assignment_list = ClientRoleAssignmentViewSet.as_view({
    "get": "list",
    "post": "create",
})
client_role_assignment_detail = ClientRoleAssignmentViewSet.as_view({
    "get": "retrieve",
    "put": "update",
    "patch": "partial_update",
    "delete": "destroy",
})


urlpatterns = [
    path('', ClientAV.as_view(), name='client'),
    path('<str:pk>', ClientAV.as_view(), name='client_id'),
    path('search/<str:term>', ClientByTermAV.as_view(), name='client_search'),
    path("client-roles/", ClientRoleViewSet.as_view(), name="client_roles"),
    path("client-roles/<uuid:pk>/", ClientRoleViewSet.as_view(), name="client_roles_id"),

    path("client-role-assignments/", client_role_assignment_list, name="client_role_assignments"),
    path("client-role-assignments/<uuid:pk>/", client_role_assignment_detail, name="client_role_assignments_id"),
]
