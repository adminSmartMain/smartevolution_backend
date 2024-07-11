from django.urls import path
from apps.misc.api.views.index import CIIUAV

urlpatterns = [
    path('', CIIUAV.as_view(), name='ciiu'),
    path('<uuid:pk>', CIIUAV.as_view(), name='ciiu_id'),
]
