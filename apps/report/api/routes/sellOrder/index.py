# views
from django.urls import path
from apps.report.api.views.index import SellOrderAV

urlpatterns = [
    path('', SellOrderAV.as_view(), name='sellOrder_detail'),
]
