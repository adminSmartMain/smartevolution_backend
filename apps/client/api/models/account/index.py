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

#se crea un modelo para manejar los logs de cambios del balance de la cuenta
class AccountBalanceHistory(BaseModel):
    OPERATION_CHOICES = [
        ('deposit', 'Deposit'),
        ('pre_operation', 'PreOperation'),
        ('refund', 'Refund'),
        ('buy_order', 'BuyOrderWH'),
        ('adjustment', 'Adjustment'),
    ]

    account         = models.ForeignKey('Account', on_delete=models.CASCADE, related_name='balance_history')
    old_balance     = models.FloatField()
    new_balance     = models.FloatField()
    amount_changed  = models.FloatField()
    operation_type  = models.CharField(max_length=20, choices=OPERATION_CHOICES)
    operation_id  = models.CharField(max_length=128)
    description  = models.CharField(max_length=128, null=True)

    class Meta:
        db_table = 'account_balance_history'
        verbose_name = 'Account Balance History'
        verbose_name_plural = 'Account Balance Histories'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.id} - Cuenta: {self.account.id} -  Tipo de Operacion: {self.operation_type} - Descripcion: {self.description}"