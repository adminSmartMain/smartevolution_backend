# views
from django.urls import path
from apps.client.api.views.index import AccountAV, AccountByClientAV

urlpatterns = [
    path('', AccountAV.as_view(), name='broker'),
    path('<uuid:pk>', AccountAV.as_view(), name='broker_id'),
    path('client/<uuid:pk>', AccountByClientAV.as_view(), name='broker_id'),
]
