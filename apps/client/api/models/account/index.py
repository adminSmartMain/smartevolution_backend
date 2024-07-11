from django.db import models

# Relations
from apps.client.api.models.client.index import Client
from apps.base.models import BaseModel


class Account(BaseModel):
    client           = models.ForeignKey(Client, on_delete=models.CASCADE)
    account_number   = models.CharField(max_length=255)  
    balance          = models.FloatField(default=0)
    primary          = models.BooleanField(default=False)
    observations     = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'account'
        verbose_name = 'account'
        verbose_name_plural = 'accounts'
        ordering = ['-created_at']