from django.db import models

# Relations
from apps.client.api.models.index import Client
from apps.base.models import BaseModel
from apps.misc.models import Bank


class FinancialCentral(BaseModel):
    client          = models.ForeignKey(Client, on_delete=models.CASCADE)
    bank            = models.ForeignKey(Bank, on_delete=models.CASCADE)
    centralBalances = models.FloatField(default=0)
    rating          = models.CharField(max_length=255, null=True)

    class Meta:
        db_table = 'FinancialCentrals'
        verbose_name = 'FinancialCentrals'
        verbose_name_plural = 'FinancialCentrals'
        ordering = ['-created_at']