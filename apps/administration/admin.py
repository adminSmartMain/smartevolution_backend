from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from apps.administration.api.models.deposit.index import Deposit
from apps.administration.api.models.emitterDeposit.index import EmitterDeposit
from apps.administration.api.models.accountingControl.index import AccountingControl
from apps.administration.api.models.refund.index import Refund

LIST_PER_PAGE = 20

class DepositResource(resources.ModelResource):
    class Meta:
        model = Deposit
        import_id_fields = ('id',)

class EmitterDepositResource(resources.ModelResource):
    class Meta:
        model = EmitterDeposit
        import_id_fields = ('id',)

class AccountingControlResource(resources.ModelResource):
    class Meta:
        model = AccountingControl
        import_id_fields = ('id',)

class RefundResource(resources.ModelResource):
    class Meta:
        model = Refund
        import_id_fields = ('id',)

@admin.register(Deposit)
class DepositAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = DepositResource
    list_display = ('id', 'amount', 'date', 'account')
    search_fields = ('id', 'account__account_number',)
    list_filter = ('date', 'amount')
    list_per_page = LIST_PER_PAGE

@admin.register(EmitterDeposit)
class EmitterDepositAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = EmitterDepositResource
    list_display = ('id', 'client', 'operation', 'accountNumber')
    search_fields = ('client__name', 'id')
    list_filter = ('accountNumber',)
    list_per_page = LIST_PER_PAGE

@admin.register(AccountingControl)
class AccountingControlAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = AccountingControlResource
    list_display = ('id', 'type', 'account')
    search_fields = ('type__description', 'account__code')
    list_filter = ('account',)
    list_per_page = LIST_PER_PAGE

@admin.register(Refund)
class RefundAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = RefundResource
    list_display = ('id', 'date', 'client', 'account')
    search_fields = ('account__code',)
    list_filter = ('date', 'id')
    list_per_page = LIST_PER_PAGE
