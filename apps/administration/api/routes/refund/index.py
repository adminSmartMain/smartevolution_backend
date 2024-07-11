# views
from django.urls import path
from apps.administration.api.views.index import RefundAV

urlpatterns = [
    path('', RefundAV.as_view(), name='refund'),
    path('<uuid:pk>', RefundAV.as_view(), name='refund_id'),
]
