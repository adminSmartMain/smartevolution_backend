# views
from django.urls import path
from apps.report.api.views.index import NegotiationSummaryAV

urlpatterns = [
    path('', NegotiationSummaryAV.as_view(), name='negotiationSummary_data'),
    path('<int:pk>', NegotiationSummaryAV.as_view(), name='negotiationSummary_detail'),
    path('<uuid:pk>', NegotiationSummaryAV.as_view(), name='negotiationSummary_detail'),
]
