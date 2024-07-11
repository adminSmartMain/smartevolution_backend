from django.urls import path
from apps.misc.api.views.index import CountryAV

urlpatterns = [
    path('', CountryAV.as_view(), name='country'),
    path('<uuid:pk>', CountryAV.as_view(), name='country_id'),
]
