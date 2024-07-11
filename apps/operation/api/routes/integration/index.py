# views
from django.urls import path
from apps.operation.api.views.index import OperationIntegrationAV

urlpatterns = [
    path('', OperationIntegrationAV.as_view(), name='integration'),
    path('<uuid:pk>', OperationIntegrationAV.as_view(), name='integration_id'),  
]