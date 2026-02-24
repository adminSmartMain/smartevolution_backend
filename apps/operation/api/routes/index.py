from django.urls import path, include


urlpatterns = [
    path('preOperation/', include('apps.operation.api.routes.preOperation.index'),name='preOperation'),
    path('receipt/', include('apps.operation.api.routes.receipt.index'),name='receipt'),
    path('buyOrder/', include('apps.operation.api.routes.buyOrder.index'),name='buyOrder'),
    path('integration/', include('apps.operation.api.routes.integration.index'),name='integration'),
    path('dashboard',include('apps.operation.api.routes.dashboard.index'),name='dashboard')
]