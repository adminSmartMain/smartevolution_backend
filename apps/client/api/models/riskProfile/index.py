from django.db import models

# Relations
from apps.client.api.models.index  import Client
from apps.misc.api.models.index    import Bank, AccountType
from apps.base.models import BaseModel


class RiskProfile(BaseModel):
    client                 = models.ForeignKey(Client, on_delete=models.CASCADE)
    gmf                    = models.BooleanField(default=False)
    iva                    = models.BooleanField(default=False)
    ica                    = models.BooleanField(default=False)
    discount_rate          = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_rate_investor = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    investor_balance       = models.FloatField(default=0)
    emitter_balance        = models.FloatField(default=0)
    payer_balance          = models.FloatField(default=0)
    bank                   = models.ForeignKey(Bank, on_delete=models.CASCADE, null=True, blank=True)
    account_type           = models.ForeignKey(AccountType, on_delete=models.CASCADE, null=True, blank=True)
    account_number         = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'riskProfile'
        verbose_name = 'riskProfile'
        verbose_name_plural = 'riskProfiles'
        ordering = ['-created_at']