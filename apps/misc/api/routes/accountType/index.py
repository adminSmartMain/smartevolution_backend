# views
from django.urls import path
from apps.misc.api.views.index import AccountTypeAV

urlpatterns = [
    path('', AccountTypeAV.as_view(), name='account_type'),
    path('<uuid:pk>', AccountTypeAV.as_view(), name='account_type_id'),
]
