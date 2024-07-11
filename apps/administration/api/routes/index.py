from django.urls import path, include

urlpatterns = [
    path('deposit/', include('apps.administration.api.routes.deposit.index'),name='deposit'),
    path('emitter-deposit/', include('apps.administration.api.routes.emitterDeposit.index'),name='emitter_deposit'),
    path('refund/', include('apps.administration.api.routes.refund.index'),name='refund'),
]