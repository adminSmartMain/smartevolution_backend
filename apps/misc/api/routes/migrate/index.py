# views
from django.urls import path
from apps.misc.api.views.index import MigrateAV

urlpatterns = [
    path('', MigrateAV.as_view(), name='migrate'),
]
