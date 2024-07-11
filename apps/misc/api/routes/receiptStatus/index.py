# views
from django.urls import path
from apps.misc.api.views.index import ReceiptStatusAV

urlpatterns = [
    path('', ReceiptStatusAV.as_view(), name='receipts-status'),
    path('<uuid:pk>', ReceiptStatusAV.as_view(), name='receipts-status_id'),
]
