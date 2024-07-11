from django.db import models
from apps.base.models import BaseModel

# Relations
from apps.client.models import Client, Account

class Deposit(BaseModel):
        
        date        = models.DateField()
        client      = models.ForeignKey(Client, on_delete=models.CASCADE)
        amount      = models.FloatField(blank=False, null=False)
        account     = models.ForeignKey(Account, on_delete=models.CASCADE)
        description = models.TextField(blank=True, null=True)
        dId         = models.IntegerField(blank=True, null=True)
    
        def __str__(self):
            return self.description if self.description else 'Sin Descripción'
    
        class Meta:
            db_table = 'deposits'
            verbose_name = 'deposit'
            verbose_name_plural = 'deposits'
            ordering = ['-created_at']

