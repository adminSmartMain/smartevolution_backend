from django.db import models
from apps.base.models import BaseModel

# Relations
from apps.misc.models import TypeExpenditure, AccountingAccount
from apps.administration.api.models.index import EmitterDeposit

class AccountingControl(BaseModel):
    type           = models.ForeignKey(TypeExpenditure, on_delete=models.CASCADE, blank=True, null=True)
    account        = models.ForeignKey(AccountingAccount, on_delete=models.CASCADE, blank=True, null=True)
    observations   = models.TextField(blank=True, null=True)
    emitterDeposit = models.ForeignKey(EmitterDeposit, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        db_table = 'accountingControls'
        verbose_name = 'accountingControl'
        verbose_name_plural = 'accountingControls'
        ordering = ['-created_at']