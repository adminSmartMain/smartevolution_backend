from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .api.models.index import (
    PreOperation,
    Receipt,
    BuyOrder,
    IntegrationHistory
)

class PreOperationResource(resources.ModelResource):
    class Meta:
        model = PreOperation
        fields = ('id', 'opType', 'emitter', 'payer', 'bill', 'amount', 'GM', 'status',)
        import_id_fields = ('id',)

class ReceiptResource(resources.ModelResource):
    class Meta:
        model = Receipt
        fields = ('id', 'date', 'account', 'realDays', 'payedAmount',)
        import_id_fields = ('id',)

class BuyOrderResource(resources.ModelResource):
    class Meta:
        model = BuyOrder
        fields = ('id', 'operation', 'code', 'name', 'status',)
        import_id_fields = ('id',)

class IntegrationHistoryResource(resources.ModelResource):
    class Meta:
        model = IntegrationHistory
        fields = ('id', 'integrationCode', 'status', 'message',)
        import_id_fields = ('id',)

@admin.register(PreOperation)
class PreOperationAdmin(ImportExportModelAdmin):
    resource_class = PreOperationResource
    list_display = ('id', 'opType', 'emitter', 'payer', 'bill', 'amount', 'GM', 'status', )
    search_fields = ('opType', 'emitter', 'payer', 'bill',)
    list_filter = ('opType', 'emitter', 'payer', 'bill',)

@admin.register(Receipt)
class ReceiptAdmin(ImportExportModelAdmin):
    resource_class = ReceiptResource
    list_display = ('id', 'date', 'account', 'realDays', 'payedAmount', )
    list_per_page = 15
    #search_fields = ('date', 'account',)
    #list_filter = ('date',)

@admin.register(BuyOrder)
class BuyOrderAdmin(ImportExportModelAdmin):
    resource_class = BuyOrderResource
    list_display = ('id', 'operation', 'code', 'name', 'status')
    search_fields = ('operation', 'code', 'name', 'status',)
    list_filter = ('operation', 'code', 'name', 'status',)

@admin.register(IntegrationHistory)
class IntegrationHistoryAdmin(ImportExportModelAdmin):
    resource_class = IntegrationHistoryResource
    list_display = ('id', 'integrationCode', 'status', 'message')
    search_fields = ('integrationCode', 'status', 'message')
    list_filter = ('integrationCode', 'status', 'message')