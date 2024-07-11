# views
from django.urls import path
from apps.client.api.views.index import ClientAV, ClientByTermAV

urlpatterns = [
    path('', ClientAV.as_view(), name='client'),
    path('<str:pk>', ClientAV.as_view(), name='client_id'),
    path('search/<str:term>', ClientByTermAV.as_view(), name='client_search'),
]
