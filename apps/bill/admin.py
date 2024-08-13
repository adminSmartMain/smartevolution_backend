from django.contrib import admin
from .api.models.index import (
    Bill,
    CreditNote,
    BillEvent,
    tempFile
)

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('id', 'billId', 'typeBill', 'emitterName', 'payerName')  # Personaliza según los campos del modelo
    search_fields = ('payerName', 'emitterName', 'billId',)  # Si "client" es una ForeignKey
    list_filter = ('payerName', 'emitterName',)

@admin.register(CreditNote)
class CreditNoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'creditNoteId', 'Bill', 'total')  # Personaliza según los campos del modelo
    search_fields = ('creditNoteId', 'Bill')  # Si "bill" es una ForeignKey
    list_filter = ('creditNoteId', 'Bill')

@admin.register(BillEvent)
class BillEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'bill', 'event', 'date')  # Personaliza según los campos del modelo
    search_fields = ('bill', 'event', 'date')  # Si "bill" es una ForeignKey
    list_filter = ('bill', 'event', 'date')

@admin.register(tempFile)
class tempFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'file', 'bill')  # Personaliza según los campos del modelo
    search_fields = ('file', 'bill')
    list_filter = ('file', 'bill')