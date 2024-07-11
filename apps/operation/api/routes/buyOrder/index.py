# views
from django.urls import path
from apps.operation.api.views.index import BuyOrderAV, BuyOrderWebhookAV

urlpatterns = [
    path('', BuyOrderAV.as_view(), name='buyOrder'),
    path('webhook', BuyOrderWebhookAV.as_view(), name='buyOrder_webhook'),
    path('<str:pk>', BuyOrderAV.as_view(), name='buyOrder_id'),
]
