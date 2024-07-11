# views
from django.urls import path
from apps.report.api.views.index import EgressReceiptAV

urlpatterns = [
    path('<uuid:pk>', EgressReceiptAV.as_view(), name='egress_receipt'),
]
