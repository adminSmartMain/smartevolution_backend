# views
from django.urls import path
from apps.misc.api.views.index import PeriodRangeAV

urlpatterns = [
    path('', PeriodRangeAV.as_view(), name='periodRange'),
    path('<uuid:pk>', PeriodRangeAV.as_view(), name='periodRange_id'),
]
