from django.contrib import admin
from apps.administration.api.models.deposit.index import Deposit
from apps.administration.api.models.emitterDeposit.index import EmitterDeposit
from apps.administration.api.models.accountingControl.index import AccountingControl
from apps.administration.api.models.refund.index import Refund

@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ('id', 'amount', 'date', 'account')  # Personaliza según los campos del modelo
    search_fields = ('account__account_number',)  # Si "account" es una ForeignKey
    list_filter = ('date', 'amount')

@admin.register(EmitterDeposit)
class EmitterDepositAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'operation', 'accountNumber')  # Personaliza según los campos del modelo
    search_fields = ('client__name', 'id')  # Si "emitter" y "deposit" son ForeignKeys
    list_filter = ('accountNumber',)

@admin.register(AccountingControl)
class AccountingControlAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'account',)  # Personaliza según los campos del modelo
    search_fields = ('type__description', 'account__code')
    list_filter = ('account',)

@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'client', 'account')  # Personaliza según los campos del modelo
    search_fields = ('account__code',)
    list_filter = ('date', 'id')