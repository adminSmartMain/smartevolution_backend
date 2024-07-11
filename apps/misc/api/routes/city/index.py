from django.urls import path
from apps.misc.api.views.index import CityAV

urlpatterns = [
    path('', CityAV.as_view(), name='city'),
    path('<uuid:pk>', CityAV.as_view(), name='city_id'),
]
