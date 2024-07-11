from django.urls import path, include

urlpatterns = [
    path('bill/', include('apps.bill.api.routes.bill.index'), name='bill')
]