from django.urls import path
from apps.misc.api.views.index import SectionAV

urlpatterns = [
    path('', SectionAV.as_view(), name='section'),
    path('<uuid:pk>', SectionAV.as_view(), name='section_id'),
]
