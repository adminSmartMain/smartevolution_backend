# views
from django.urls import path
from apps.misc.api.views.index import TypeClientAV

urlpatterns = [
    path('', TypeClientAV.as_view(), name='type_client'),
    path('<uuid:pk>', TypeClientAV.as_view(), name='type_client_id'),
]
