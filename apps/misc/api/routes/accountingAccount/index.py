# views
from django.urls import path
from apps.misc.api.views.index import AccountingAccountAV

urlpatterns = [
    path('', AccountingAccountAV.as_view(), name='accounting-account'),
    path('<str:pk>', AccountingAccountAV.as_view(), name='accounting-account_id'),
]
