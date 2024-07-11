# views
from django.urls import path
from apps.client.api.views.index import BrokerAV, BrokerByClientAV

urlpatterns = [
    path('', BrokerAV.as_view(), name='broker'),
    path('<str:pk>', BrokerAV.as_view(), name='broker_id'),
    path('client/<str:pk>', BrokerByClientAV.as_view(), name='broker_by_client'),
]
