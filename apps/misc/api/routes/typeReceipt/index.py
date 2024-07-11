# views
from django.urls import path
from apps.misc.api.views.index import TypeReceiptAV

urlpatterns = [
    path('', TypeReceiptAV.as_view(), name='typeReceipt'),
    path('<uuid:pk>', TypeReceiptAV.as_view(), name='typeReceipt_id'),
]
