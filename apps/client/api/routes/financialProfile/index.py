# views
from django.urls import path
from apps.client.api.views.index import FinancialProfileAV, FinancialProfileIndicatorsAV, AssetsAV, PassivesAV, PatrimonyAV, StateOfResultAV

urlpatterns = [
    path('', FinancialProfileAV.as_view(), name='financial-profile'),
    path('<uuid:pk>', FinancialProfileAV.as_view(), name='financial-profile-id_patch'),
    path('<uuid:pk>/<int:periods>', FinancialProfileAV.as_view(), name='financial-profile-id'),
    path('indicators/<uuid:pk>', FinancialProfileIndicatorsAV.as_view(), name='financial-profile-indicators'),
    path('assets/<uuid:pk>', AssetsAV.as_view(), name='financial-profile-assets_id'),
    path('passives/<uuid:pk>', PassivesAV.as_view(), name='financial-profile-passives_id'),
    path('patrimony/<uuid:pk>', PatrimonyAV.as_view(), name='financial-profile-patrimony_id'),
    path('state-of-result/<uuid:pk>', StateOfResultAV.as_view(), name='financial-profile-state-of-result_id'),
    path('assets', AssetsAV.as_view(), name='financial-profile-assets'),
    path('passives', PassivesAV.as_view(), name='financial-profile-passives'),
    path('patrimony', PatrimonyAV.as_view(), name='financial-profile-patrimony'),
    path('state-of-result', StateOfResultAV.as_view(), name='financial-profile-state-of-result'),
]
