from django.urls import path, include

urlpatterns = [
    path('account_type/', include('apps.misc.api.routes.accountType.index'),name='account_type'),
    path('activity/', include('apps.misc.api.routes.activity.index'),name='activity'),
    path('bank/', include('apps.misc.api.routes.bank.index'),name='bank'),
    path('ciiu/', include('apps.misc.api.routes.ciiu.index'),name='ciiu'),
    path('city/', include('apps.misc.api.routes.city.index'),name='city'),
    path('department/', include('apps.misc.api.routes.department.index'),name='department'),
    path('section/', include('apps.misc.api.routes.section.index'),name='section'),
    path('type_client/', include('apps.misc.api.routes.typeClient.index'),name='type_client'),
    path('type_identity/', include('apps.misc.api.routes.typeIdentity.index'),name='type_identity'),
    path('country/', include('apps.misc.api.routes.country.index'),name='country'),
    path('type_expenditure/', include('apps.misc.api.routes.typeExpenditure.index'),name='type_expenditure'),
    path('accounting_account/', include('apps.misc.api.routes.accountingAccount.index'),name='accounting_account'),
    path('type_event/', include('apps.misc.api.routes.typeEvent.index'),name='type_event'),
    path('type_operation/', include('apps.misc.api.routes.typeOperation.index'),name='type_operation'),
    path('type_receipt/', include('apps.misc.api.routes.typeReceipt.index'),name='type_receipt'),
    path('type_period/', include('apps.misc.api.routes.typePeriod.index'),name='type_period'),
    path('period_range/', include('apps.misc.api.routes.periodRange.index'),name='period_range'),
    path('receipt_status/', include('apps.misc.api.routes.receiptStatus.index'),name='receipt_status'),
    path('test/', include('apps.misc.api.routes.test.index'),name='test'),
    path('migrate/', include('apps.misc.api.routes.migrate.index'),name='migrate'),
]