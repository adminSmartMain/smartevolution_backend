# views
from django.urls import path
from apps.report.api.views.index import MessagesTestAV, TwilioMessageHandlerAV, SignatureAV

urlpatterns = [
    path('buyOrder', MessagesTestAV.as_view(), name='messagesbo'),
    path('buyOrder/<uuid:pk>', MessagesTestAV.as_view(), name='messagesbo_id'),
    path('twilio', TwilioMessageHandlerAV.as_view(), name='twilio'),
    path('signature', SignatureAV.as_view(), name='signature'),
]
