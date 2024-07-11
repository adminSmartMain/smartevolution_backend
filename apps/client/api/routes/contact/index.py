# views
from django.urls import path
from apps.client.api.views.index import ContactAV

urlpatterns = [
    path('', ContactAV.as_view(), name='contact'),
    path('<uuid:pk>', ContactAV.as_view(), name='contact_id'),
]
