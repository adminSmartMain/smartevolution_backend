
from django.urls import path
# views
from apps.client.api.views.index import RiskProfileAV, RiskProfileByClientAV
from apps.client.api.views.riskProfile.index import LevelRiskViewSet

urlpatterns = [
    path('', RiskProfileAV.as_view(), name='risk_profile'),
    path('<uuid:pk>', RiskProfileAV.as_view(), name='risk_profile_id'),
    path('client/<uuid:pk>', RiskProfileByClientAV.as_view(), name='risk_profile_id_client'),
    path('level-risk/', LevelRiskViewSet.as_view(), name='level_risk'),
    path('level-risk/<uuid:pk>/', LevelRiskViewSet.as_view(), name='level_risk_id'),

]