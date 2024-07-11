from django.urls import path
from apps.misc.api.views.index import ActivityAV

urlpatterns = [
    path('', ActivityAV.as_view(), name='activity'),
    path('<uuid:pk>', ActivityAV.as_view(), name='activity_id'),
]
