
from django.urls import path
# views
from apps.client.api.views.index import LegalClientAV, NaturalClientAV

urlpatterns = [
    path('legalClient', LegalClientAV.as_view(), name='risk_profile'),
    path('legalClient/<uuid:pk>', LegalClientAV.as_view(), name='risk_profile'),
    path('naturalClient', NaturalClientAV.as_view(), name='risk_profile'),
    path('naturalClient/<uuid:pk>', NaturalClientAV.as_view(), name='risk_profile'),
]
