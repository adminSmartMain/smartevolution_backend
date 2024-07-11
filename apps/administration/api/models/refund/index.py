from django.db import models
from apps.base.models import BaseModel

# Relations
from apps.client.models    import Client, Account
from apps.misc.models      import Bank, AccountType

class Refund(BaseModel):
    date          = models.DateField()
    client        = models.ForeignKey(Client, on_delete=models.CASCADE)
    account       = models.ForeignKey(Account, on_delete=models.CASCADE)
    amount        = models.FloatField(blank=True, null=True)
    applyGM       = models.BooleanField(default=True)
    gmAmount      = models.FloatField(blank=True, null=True)
    beneficiary   = models.CharField(max_length=255, blank=True, null=True)
    bank          = models.ForeignKey(Bank, on_delete=models.CASCADE, blank=True, null=True)
    accountType   = models.ForeignKey(AccountType, on_delete=models.CASCADE, blank=True, null=True)
    accountNumber = models.CharField(max_length=255, blank=True, null=True)
    observations  = models.TextField(blank=True, null=True)
    rId           = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'refunds'
        verbose_name = 'refund'
        verbose_name_plural = 'refunds'
        ordering = ['-created_at']
