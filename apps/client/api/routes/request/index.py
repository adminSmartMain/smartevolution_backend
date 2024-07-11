# views
from django.urls import path
from apps.client.api.views.index import RequestAV

urlpatterns = [
    path('', RequestAV.as_view(), name='request'),
    path('<uuid:pk>', RequestAV.as_view(), name='request_id'),
]
