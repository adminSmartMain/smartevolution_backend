from django.db import models
from apps.base.models import BaseModel
from ..bill.index import Bill

#Comentarios
class CreditNote(BaseModel):
    creditNoteId      = models.CharField(max_length=255, unique=True)
    Bill              = models.ForeignKey(Bill, on_delete=models.CASCADE)
    associatedInvoice = models.CharField(max_length=255)
    total             = models.FloatField()

    class Meta:
        db_table = 'creditNotes'
        ordering = ['-created_at']