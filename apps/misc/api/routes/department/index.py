from django.urls import path
from apps.misc.api.views.index import DepartmentAV

urlpatterns = [
    path('', DepartmentAV.as_view(), name='department'),
    path('<uuid:pk>', DepartmentAV.as_view(), name='department_id'),
]
