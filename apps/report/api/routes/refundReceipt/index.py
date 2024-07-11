# views
from django.urls import path
from apps.report.api.views.index import RefundReceiptAV
urlpatterns = [
    path('<str:pk>', RefundReceiptAV.as_view(), name='refundReceiptAV'),
]
