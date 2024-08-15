from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .api.models.index import (
    PreOperation,
    Receipt,
    BuyOrder,
    IntegrationHistory
)

LIST_PER_PAGE = 20

class PreOperationResource(resources.ModelResource):
    class Meta:
        model = PreOperation    
        fields = '__all__'
        import_id_fields = ('id',)

class ReceiptResource(resources.ModelResource):
    class Meta:
        model = Receipt
        fields = '__all__'
        import_id_fields = ('id',)

class BuyOrderResource(resources.ModelResource):
    class Meta:
        model = BuyOrder
        fields = '__all__'
        import_id_fields = ('id',)

class IntegrationHistoryResource(resources.ModelResource):
    class Meta:
        model = IntegrationHistory
        fields = '__all__'
        import_id_fields = ('id',)

@admin.register(PreOperation)
class PreOperationAdmin(ImportExportModelAdmin):
    resource_class = PreOperationResource
    list_display = ('id', 'opType', 'emitter', 'payer', 'bill', 'amount', 'GM', 'status', )
    search_fields = ('opType', 'emitter', 'payer', 'bill',)
    list_filter = ('opType', 'emitter', 'payer', 'bill',)
    list_per_page = LIST_PER_PAGE  # Usa la variable constante para la paginación

@admin.register(Receipt)
class ReceiptAdmin(ImportExportModelAdmin):
    resource_class = ReceiptResource
    list_display = ('id', 'date', 'account', 'payedAmount', )
    list_per_page = LIST_PER_PAGE  # Usa la variable constante para la paginación
    list_select_related = ('account',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('account')

@admin.register(BuyOrder)
class BuyOrderAdmin(ImportExportModelAdmin):
    resource_class = BuyOrderResource
    list_display = ('id', 'operation', 'code', 'name', 'status')
    search_fields = ('operation', 'code', 'name', 'status',)
    list_filter = ('operation', 'code', 'name', 'status',)
    list_per_page = LIST_PER_PAGE  # Usa la variable constante para la paginación

@admin.register(IntegrationHistory)
class IntegrationHistoryAdmin(ImportExportModelAdmin):
    resource_class = IntegrationHistoryResource
    list_display = ('id', 'integrationCode', 'status', 'message')
    search_fields = ('integrationCode', 'status', 'message')
    list_filter = ('integrationCode', 'status', 'message')
    list_per_page = LIST_PER_PAGE  # Usa la variable constante para la paginación
