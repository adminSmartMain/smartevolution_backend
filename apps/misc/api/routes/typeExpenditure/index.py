# views
from django.urls import path
from apps.misc.api.views.index import TypeExpenditureAV

urlpatterns = [
    path('', TypeExpenditureAV.as_view(), name='type_expenditure'),
    path('<uuid:pk>', TypeExpenditureAV.as_view(), name='type_expenditure_id'),
]
