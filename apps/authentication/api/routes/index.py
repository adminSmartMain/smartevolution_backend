from django.urls import path, include

urlpatterns = [
    path('auth/', include('apps.authentication.api.routes.authentication.index')),
    path('user/', include('apps.authentication.api.routes.user.index')),
    path('access-control/', include('apps.authentication.api.routes.access_control')),
]
