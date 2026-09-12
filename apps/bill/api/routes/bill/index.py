# views
from django.urls import path
from apps.bill.api.views.index import BillAV, readBillAV, readCreditNoteAV, BillCreationManualAV, PendingBillyBillsAV, BillWatchlistAV, BillSyncNowAV

urlpatterns = [
    path('read', readBillAV.as_view(), name='bill'),
    path('billy-pending', PendingBillyBillsAV.as_view(), name='billy-pending'),
    path('watchlist/<uuid:pk>', BillWatchlistAV.as_view(), name='bill-watchlist'),
    path('sync-now/<uuid:pk>', BillSyncNowAV.as_view(), name='bill-sync-now'),
    path('', BillAV.as_view(), name='bill'),
    path('<str:pk>', BillAV.as_view(), name='bill_id'),
    path('<uuid:pk>', BillAV.as_view(), name='bill_uuid'),
    path('read/credit-note', readCreditNoteAV.as_view(), name='credit_note'),
    path('save_bill/', BillCreationManualAV.as_view(), name='bill-create'),
    
]
