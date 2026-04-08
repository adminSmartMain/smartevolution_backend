# views
from django.urls import path
from apps.operation.api.views.index import (PreOperationAV, GetLastOperationAV, 
                                            GetBillFractionAV,GetBillFractionBulkAV, GetOperationByEmitter, 
                                            GetOperationByParams, OperationDetailAV, MassiveOperations,UploadExcel,RegisterOperationFromUpload, ClientsWithAccountsAV,MassiveOperationReceiptPDFAV)

urlpatterns = [
    path('', PreOperationAV.as_view(), name='preOperation'),
    path('<uuid:pk>', PreOperationAV.as_view(), name='preOperation_id'),
    path('<int:pk>', PreOperationAV.as_view(), name='preOperation_id_delete'),
    path('last', GetLastOperationAV.as_view(), name='last_operation'),
    path('billFraction/<uuid:pk>', GetBillFractionAV.as_view(), name='bill_fraction'),
    path('emitter/<uuid:pk>', GetOperationByEmitter.as_view(), name='operation_by_emitter'),
    path('params', GetOperationByParams.as_view(), name='operation_by_params'),
    path('detail/<int:pk>', OperationDetailAV.as_view(), name='operation_detail'),
    path("uploadExcel", UploadExcel.as_view(), name="upload_excel"),
    path("registerOperationFromUpload", RegisterOperationFromUpload.as_view(), name="register_operation_from_upload"),
    path('billFractionBulk', GetBillFractionBulkAV.as_view(), name='bill_fraction_bulk'),
    path("clientsWithAccounts", ClientsWithAccountsAV.as_view(), name="clients_with_accounts"),
    path("massive-receipt/<int:op_id>",MassiveOperationReceiptPDFAV.as_view(),name="massive-operation-receipt-pdf",),
]
