from django.contrib import admin
from .api.models.index import (
    PreOperation,
    Receipt,
    BuyOrder,
    IntegrationHistory
)

@admin.register(PreOperation)
class PreOperationAdmin(admin.ModelAdmin):
    list_display = ('id', 'opType', 'emitter', 'payer', 'bill', 'amount', 'GM', 'status', )
    search_fields = ('opType', 'emitter', 'payer', 'bill',)
    list_filter = ('opType', 'emitter', 'payer', 'bill',)

@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'account', 'realDays', 'payedAmount', )
    search_fields = ('date', 'account', 'realDays', 'payedAmount',)
    list_filter = ('date', 'account', 'realDays', 'payedAmount',)

@admin.register(BuyOrder)
class BuyOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'operation', 'code', 'name', 'status')
    search_fields = ('operation', 'code', 'name', 'status',)
    list_filter = ('operation', 'code', 'name', 'status',)

@admin.register(IntegrationHistory)
class IntegrationHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'integrationCode', 'status', 'message')
    search_fields = ('integrationCode', 'status', 'message')
    list_filter = ('integrationCode', 'status', 'message')