from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .api.models.index import (
    Bill,
    CreditNote,
    BillEvent,
    tempFile
)

LIST_PER_PAGE = 20

class BillResource(resources.ModelResource):
    class Meta:
        model = Bill
        import_id_fields = ('id',)

class CreditNoteResource(resources.ModelResource):
    class Meta:
        model = CreditNote
        import_id_fields = ('creditNoteId',)

class BillEventResource(resources.ModelResource):
    class Meta:
        model = BillEvent
        import_id_fields = ('id',)

class tempFileResource(resources.ModelResource):
    class Meta:
        model = tempFile
        import_id_fields = ('id',)

@admin.register(Bill)
class BillAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = BillResource
    list_display = ('id', 'billId', 'typeBill', 'emitterName', 'payerName', 'created_at')
    search_fields = ('billId', 'emitterName', 'payerName')
    list_filter = ('typeBill', 'emitterName', 'payerName')
    list_per_page = LIST_PER_PAGE

@admin.register(CreditNote)
class CreditNoteAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = CreditNoteResource
    list_display = ('id', 'creditNoteId', 'Bill', 'total')
    search_fields = ('creditNoteId', 'Bill')
    list_filter = ('Bill', 'creditNoteId')
    list_per_page = LIST_PER_PAGE

@admin.register(BillEvent)
class BillEventAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = BillEventResource
    list_display = ('id', 'bill', 'event', 'date', 'created_at')
    search_fields = ('bill__billId', 'event', 'date')  # Asume que 'bill' es una ForeignKey
    list_filter = ('bill', 'event', 'date')
    list_per_page = LIST_PER_PAGE

@admin.register(tempFile)
class tempFileAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = tempFileResource
    list_display = ('id', 'file', 'bill')
    search_fields = ('file', 'bill__billId')  # Asume que 'bill' es una ForeignKey
    list_filter = ('bill',)
    list_per_page = LIST_PER_PAGE