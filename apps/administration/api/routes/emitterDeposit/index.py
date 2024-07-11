# views
from django.urls import path
from apps.administration.api.views.index import EmitterDepositAV

urlpatterns = [
    path('', EmitterDepositAV.as_view(), name='emitter_deposit'),
    path('<uuid:pk>', EmitterDepositAV.as_view(), name='emitter_deposit'),
]
