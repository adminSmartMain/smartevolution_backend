# views
from django.urls import path
from apps.report.api.views.index import PurchaseOrderAV

urlpatterns = [
    path('', PurchaseOrderAV.as_view(), name='purchaseOrder_detail'),
    path('<int:pk>', PurchaseOrderAV.as_view(), name='purchaseOrder_detail'),
]
