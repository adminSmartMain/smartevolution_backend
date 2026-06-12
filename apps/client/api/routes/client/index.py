# views
from django.urls import path
from apps.client.api.views.index import ClientAV, ClientByTermAV,ClientsWithActiveOperationsAV

urlpatterns = [
        path(
        "with-active-operations/",
        ClientsWithActiveOperationsAV.as_view(),
        name="clients_with_active_operations",
    ),
    path('', ClientAV.as_view(), name='client'),
    path('<str:pk>', ClientAV.as_view(), name='client_id'),
    path('search/<str:term>', ClientByTermAV.as_view(), name='client_search'),
]
