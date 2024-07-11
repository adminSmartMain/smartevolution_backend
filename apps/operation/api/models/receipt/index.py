from django.db import models
from apps.base.models import BaseModel

# relations with other models
from apps.client.api.models.index import Account
from apps.operation.api.models.index import PreOperation
from apps.bill.models import Bill
from apps.misc.models import TypeReceipt, ReceiptStatus


class Receipt(BaseModel):
    dId                      = models.IntegerField(default=0)
    date                     = models.DateField()
    operation                = models.ForeignKey(PreOperation, on_delete=models.CASCADE)
    typeReceipt              = models.ForeignKey(TypeReceipt, on_delete=models.CASCADE)
    receiptStatus            = models.ForeignKey(ReceiptStatus, on_delete=models.CASCADE, blank=True, null=True)
    account                  = models.ForeignKey(Account, on_delete=models.CASCADE, blank=True, null=True)
    realDays                 = models.IntegerField(default=0)
    additionalDays           = models.IntegerField(default=0)
    calculatedDays           = models.IntegerField(default=0)
    additionalInterests      = models.FloatField(default=0)
    additionalInterestsSM    = models.FloatField(default=0)
    investorInterests        = models.FloatField(default=0)
    tableInterests           = models.FloatField(default=0)
    futureValueRecalculation = models.FloatField(default=0)
    tableRemaining           = models.FloatField(default=0)
    remaining                = models.FloatField(default=0)
    payedAmount              = models.FloatField(default=0)
    presentValueInvestor     = models.FloatField(default=0)
    
    

    def __str__(self):
        return self.operation.bill.billId

    class Meta:
        db_table = 'receipts'
        verbose_name = 'Receipt'
        verbose_name_plural = 'Receipts'
        ordering = ['-created_at']
