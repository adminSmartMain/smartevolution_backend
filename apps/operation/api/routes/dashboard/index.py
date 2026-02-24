from django.urls import path
from apps.operation.api.views.dashboard.index import DashboardAV



urlpatterns = [
    path('', DashboardAV.as_view(), name='dashboard'),
   
]
