# views
from django.urls import path
from apps.bill.api.views.index import BillAV, readBillAV, readCreditNoteAV

urlpatterns = [
    path('read', readBillAV.as_view(), name='bill'),
    path('', BillAV.as_view(), name='bill'),
    path('<str:pk>', BillAV.as_view(), name='bill_id'),
    path('<uuid:pk>', BillAV.as_view(), name='bill_uuid'),
    path('read/credit-note', readCreditNoteAV.as_view(), name='credit_note'),
]
