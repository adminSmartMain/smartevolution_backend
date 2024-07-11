# views
from django.urls import path
from apps.misc.api.views.index import TypePeriodAV

urlpatterns = [
    path('', TypePeriodAV.as_view(), name='typePeriod'),
    path('<uuid:pk>', TypePeriodAV.as_view(), name='typePeriod_id'),
]
