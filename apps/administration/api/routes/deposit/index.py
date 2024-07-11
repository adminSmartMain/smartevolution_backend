# views
from django.urls import path
from apps.administration.api.views.index import DepositAV

urlpatterns = [
    path('', DepositAV.as_view(), name='deposit'),
    path('<uuid:pk>', DepositAV.as_view(), name='deposit'),
]
