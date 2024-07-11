# views
from django.urls import path
from apps.misc.api.views.index import TypeIdentityAV

urlpatterns = [
    path('', TypeIdentityAV.as_view(), name='type_identity'),
    path('<uuid:pk>', TypeIdentityAV.as_view(), name='type_identity_id'),
]
