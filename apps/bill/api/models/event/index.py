from django.db import models
from apps.base.models import BaseModel
from ..bill.index import Bill
from apps.misc.models import TypeEvent


class BillEvent(BaseModel):
    bill        = models.ForeignKey(Bill, on_delete=models.CASCADE)
    event       = models.ForeignKey(TypeEvent, on_delete=models.CASCADE)
    date = models.DateTimeField() 


    class Meta:
        db_table = 'billEvent'
        ordering = ['-created_at']
