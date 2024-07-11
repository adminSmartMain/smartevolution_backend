# views
from django.urls import path
from apps.client.api.views.index import technicalDataAV

urlpatterns = [
    path('', technicalDataAV.as_view(), name='technicalData'),
    path('<str:pk>', technicalDataAV.as_view(), name='technicalData_id'),
]
