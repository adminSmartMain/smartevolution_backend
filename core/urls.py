from django.contrib import admin
from django.urls import path, include
from apps.misc.api.views.test.index import TestAV

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.authentication.api.routes.index'), name='auth'),
    path('api/', include('apps.misc.api.routes.index'), name='misc'),
    path('api/', include('apps.client.api.routes.index'), name='client'),
    path('api/', include('apps.bill.api.routes.index'), name='bill'),
    path('api/', include('apps.operation.api.routes.index'), name='operation'),
    path('api/', include('apps.report.api.routes.index'), name='report'),
    path('api/', include('apps.administration.api.routes.index'), name='administration'),
    #path('api/migrate', TestAV.as_view(), name='migration'),
]
