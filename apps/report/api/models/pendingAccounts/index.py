from django.db import models
from apps.base.models import BaseModel
from apps.client.models import Client
from apps.misc.models import AccountingAccount, TypeExpenditure

class PendingAccount(BaseModel):
    opId        = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    amount      = models.FloatField(default=0) 
    date        = models.DateField( blank=True, null=True)
    third       = models.ForeignKey(Client, on_delete=models.CASCADE, blank=True, null=True)
    accountingControl = models.ForeignKey(AccountingAccount, on_delete=models.CASCADE, blank=True, null=True)
    typeExpenditure   = models.ForeignKey(TypeExpenditure, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        db_table = 'pendingAccount'
        verbose_name = 'PendingAccount'
        verbose_name_plural = 'PendingAccounts'
        ordering = ['-created_at']