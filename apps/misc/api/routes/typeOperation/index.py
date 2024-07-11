# views
from django.urls import path
from apps.misc.api.views.index import TypeOperationAV

urlpatterns = [
    path('', TypeOperationAV.as_view(), name='typeOperation'),
    path('<uuid:pk>', TypeOperationAV.as_view(), name='typeOperation_id'),
]
