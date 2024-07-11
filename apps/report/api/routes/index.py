from django.urls import path, include

urlpatterns = [
    path('report/sellOrder/', include('apps.report.api.routes.sellOrder.index'),name='purchaseOrder'),
    path('report/purchaseOrder/', include('apps.report.api.routes.purchaseOrder.index'),name='sellOrder'),
    path('report/egressReceipt/', include('apps.report.api.routes.egressReceipt.index'),name='egressReceipt'),
    path('report/refundReceipt/', include('apps.report.api.routes.refundReceipt.index'),name='refundReceipt'),
    path('report/negotiationSummary/', include('apps.report.api.routes.negotiationSummary.index'),name='negotiationSummary'),
    path('report/messages/', include('apps.report.api.routes.messages.index'),name='messages'),
]