from django.urls import path
from apps.operation.api.views.index import (
    ReceiptAV,
    MassiveReceiptPreview,
    MassiveReceiptRegister,
    MassiveReceiptUploadExcel,
    ReceiptVoidAV,
    ReceiptAdjustAV,
    ReceiptHistoryAV,
)


urlpatterns = [
    path("", ReceiptAV.as_view(), name="receipt"),
    path("history/", ReceiptHistoryAV.as_view(), name="receipt_history"),
    path("<uuid:pk>/void/", ReceiptVoidAV.as_view(), name="receipt_void"),
    path("<uuid:pk>/adjust/", ReceiptAdjustAV.as_view(), name="receipt_adjust"),
    path("<uuid:pk>", ReceiptAV.as_view(), name="receipt_id"),

    path(
        "preOperation/massive-receipt/preview/",
        MassiveReceiptPreview.as_view(),
        name="massive-receipt-preview",
    ),
    path(
        "preOperation/massive-receipt/upload-excel/",
        MassiveReceiptUploadExcel.as_view(),
        name="massive-receipt-upload-excel",
    ),
    path(
        "preOperation/massive-receipt/register/",
        MassiveReceiptRegister.as_view(),
        name="massive-receipt-register",
    ),
]