
from django.urls import path
# views
from apps.client.api.views.index import RiskProfileAV, RiskProfileByClientAV

urlpatterns = [
    path('', RiskProfileAV.as_view(), name='risk_profile'),
    path('<uuid:pk>', RiskProfileAV.as_view(), name='risk_profile_id'),
    path('client/<uuid:pk>', RiskProfileByClientAV.as_view(), name='risk_profile_id_client')
]
