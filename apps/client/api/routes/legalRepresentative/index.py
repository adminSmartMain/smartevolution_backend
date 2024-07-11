# views
from django.urls import path
from apps.client.api.views.index import LegalRepresentativeAV

urlpatterns = [
    path('', LegalRepresentativeAV.as_view(), name='legalRepresentative'),
    path('<uuid:pk>', LegalRepresentativeAV.as_view(), name='legalRepresentative_id'),
]
