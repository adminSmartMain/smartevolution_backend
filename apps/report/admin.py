from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .api.models.index import (
    PendingAccount,
    NegotiationSummary,
    SellOrder,
    SellOrderOperation
)

LIST_PER_PAGE = 20

class PendingAccountResource(resources.ModelResource):
    class Meta:
        model = PendingAccount
        fields = '__all__'
        import_id_fields = ('id',)

class NegotiationSummaryResource(resources.ModelResource):
    class Meta:
        model = NegotiationSummary
        fields = '__all__'
        import_id_fields = ('id',)

class SellOrderResource(resources.ModelResource):
    class Meta:
        model = SellOrder
        fields = '__all__'
        import_id_fields = ('id',)

class SellOrderOperationResource(resources.ModelResource):
    class Meta:
        model = SellOrderOperation
        fields = '__all__'
        import_id_fields = ('id',)

@admin.register(PendingAccount)
class PendingAccountAdmin(ImportExportModelAdmin):
    resource_class = PendingAccountResource
    list_display = ('id', 'opId', 'description', 'amount', 'date', )
    search_fields = ('opId', 'description', 'amount', 'date',)
    list_filter = ('opId', 'description', 'amount', 'date',)
    list_per_page = LIST_PER_PAGE

@admin.register(NegotiationSummary)
class NegotiationSummaryAdmin(ImportExportModelAdmin):
    resource_class = NegotiationSummaryResource
    list_display = ('id', 'opId', 'emitter', 'payer', 'commissionValueBeforeTaxes', 'iva', 'total', )
    search_fields = ('opId', 'emitter', 'payer', 'commissionValueBeforeTaxes', 'iva', 'total',)
    list_filter = ('opId', 'emitter', 'payer', 'commissionValueBeforeTaxes', 'iva', 'total',)
    list_per_page = LIST_PER_PAGE

@admin.register(SellOrder)
class SellOrderAdmin(ImportExportModelAdmin):
    resource_class = SellOrderResource
    list_display = ('id', 'client', 'opId', 'status',)
    search_fields = ('client', 'opId', 'status',)
    list_filter = ('client', 'opId', 'status',)
    list_per_page = LIST_PER_PAGE

@admin.register(SellOrderOperation)
class SellOrderOperationAdmin(ImportExportModelAdmin):
    resource_class = SellOrderOperationResource
    list_display = ('id', 'sellOrder', 'operation')
    search_fields = ('sellOrder', 'operation')
    list_filter = ('sellOrder', 'operation')
    list_per_page = LIST_PER_PAGE