# views
from django.urls import path
from apps.client.api.views.index import OverviewAV

urlpatterns = [
    path('', OverviewAV.as_view(), name='overview'),
    path('<str:pk>', OverviewAV.as_view(), name='overview_id'),
]
