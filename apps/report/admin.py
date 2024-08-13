from django.contrib import admin
from .api.models.index import (
    PendingAccount,
    NegotiationSummary,
    SellOrder,
    SellOrderOperation
    )

@admin.register(PendingAccount)
class PendingAccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'opId', 'description', 'amount', 'date', )
    search_fields = ('opId', 'description', 'amount', 'date',)
    list_filter = ('opId', 'description', 'amount', 'date',)

@admin.register(NegotiationSummary)
class NegotiationSummaryAdmin(admin.ModelAdmin):
    list_display = ('id', 'opId', 'emitter', 'payer', 'commissionValueBeforeTaxes', 'iva', 'total', )
    search_fields = ('opId', 'emitter', 'payer', 'commissionValueBeforeTaxes', 'iva', 'total',)
    list_filter = ('opId', 'emitter', 'payer', 'commissionValueBeforeTaxes', 'iva', 'total',)

@admin.register(SellOrder)
class SellOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'opId', 'status',)
    search_fields = ('client', 'opId', 'status',)
    list_filter = ('client', 'opId', 'status',)

@admin.register(SellOrderOperation)
class SellOrderOperationAdmin(admin.ModelAdmin):
    list_display = ('id', 'sellOrder', 'operation')
    search_fields = ('sellOrder', 'operation')
    list_filter = ('sellOrder', 'operation')