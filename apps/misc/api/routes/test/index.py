# views
from django.urls import path
from apps.misc.api.views.index import TestAV

urlpatterns = [
    path('', TestAV.as_view(), name='test'),
    path('<uuid:pk>', TestAV.as_view(), name='test_id'),
]