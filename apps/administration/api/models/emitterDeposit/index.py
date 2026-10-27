from django.db import models
from apps.base.models import BaseModel

# Relations
from apps.client.models    import Client
from apps.operation.models import PreOperation
from apps.misc.models      import Bank, AccountType

class EmitterDeposit(BaseModel):
    date          = models.DateField()
    client        = models.ForeignKey(Client, on_delete=models.CASCADE)
    operation     = models.ForeignKey(PreOperation, on_delete=models.CASCADE, blank=True, null=True)
    amount        = models.FloatField(blank=False, null=False)
    # Legal settlement value for COP disbursements. Legacy ``amount`` remains
    # for historic compatibility; new disbursements always populate this field.
    settledAmount = models.DecimalField(max_digits=18, decimal_places=0, null=True, blank=True)
    bank          = models.ForeignKey(Bank, on_delete=models.CASCADE)
    beneficiary   = models.CharField(max_length=255, blank=False, null=False)
    accountType   = models.ForeignKey(AccountType, on_delete=models.CASCADE)
    accountNumber = models.CharField(max_length=255, blank=False, null=False)
    edId          = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'emitterDeposits'
        verbose_name = 'emitterDeposit'
        verbose_name_plural = 'emitterDeposits'
        ordering = ['-created_at']
