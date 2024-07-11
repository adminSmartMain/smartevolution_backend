# views
from django.urls import path
from apps.operation.api.views.index import ReceiptAV

urlpatterns = [
    path('', ReceiptAV.as_view(), name='receipt'),
    path('<uuid:pk>', ReceiptAV.as_view(), name='receipt_id'),  
]