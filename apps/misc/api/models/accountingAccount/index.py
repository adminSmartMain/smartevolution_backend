from django.db import models
from apps.base.models import BaseModel


class AccountingAccount(BaseModel):
    code          = models.CharField(max_length=255, blank=True)
    description   = models.TextField(blank=True)
    accountNumber = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'accountingAccounts'
        verbose_name = 'accountingAccount'
        verbose_name_plural = 'accountingAccounts'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.description
