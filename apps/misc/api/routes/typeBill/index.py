# views
from django.urls import path
from apps.misc.api.views.index import TypeBillAV

urlpatterns = [
    path('',TypeBillAV.as_view(), name='type_billl'),
    path('<uuid:pk>', TypeBillAV.as_view(), name='type_bill_id'),
]
