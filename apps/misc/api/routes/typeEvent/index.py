# views
from django.urls import path
from apps.misc.api.views.index import TypeEventAV

urlpatterns = [
    path('', TypeEventAV.as_view(), name='typeEvent'),
    path('<uuid:pk>', TypeEventAV.as_view(), name='typeEvent_id'),
]
