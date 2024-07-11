from django.urls import path
from apps.misc.api.views.index import BankAV

urlpatterns = [
    path('', BankAV.as_view(), name='bank'),
    path('<uuid:pk>', BankAV.as_view(), name='bank_id'),
]
