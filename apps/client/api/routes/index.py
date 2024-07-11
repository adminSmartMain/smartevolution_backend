from django.urls import path, include

urlpatterns = [
    path('broker/', include('apps.client.api.routes.broker.index'), name='broker'),
    path('client/', include('apps.client.api.routes.client.index'), name='client'),
    path('contact/', include('apps.client.api.routes.contact.index'), name='client_contact'),
    path('request/', include('apps.client.api.routes.request.index'), name='request'),
    path('riskProfile/', include('apps.client.api.routes.riskProfile.index'), name='risk_profile'),
    path('account/', include('apps.client.api.routes.account.index'), name='account'),
    path('legalRepresentative/', include('apps.client.api.routes.legalRepresentative.index'), name='legal_representative'),
    path('financialProfile/', include('apps.client.api.routes.financialProfile.index'), name='financial_profile'),
    path('overview/', include('apps.client.api.routes.overview.index'), name='overview'),
    path('technicalData/', include('apps.client.api.routes.technicalData.index'), name='technical_data'),
    path('selfManagement/', include('apps.client.api.routes.selfManagement.index'), name='self_management'),
]