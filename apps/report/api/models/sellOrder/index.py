from django.db import models
from apps.base.models import BaseModel
from apps.client.api.models.index import Client

class SellOrder(BaseModel):
    file        = models.FileField(upload_to='sellOrder', blank=True, null=True)
    client      = models.ForeignKey(Client, on_delete=models.CASCADE, blank=True, null=True)
    approveCode = models.CharField(max_length=255, blank=True, null=True)
    rejectCode  = models.CharField(max_length=255, blank=True, null=True)
    opId        = models.CharField(max_length=255, blank=True, null=True)
    status      = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'sellOrder'
        verbose_name = 'sellOrder'
        verbose_name_plural = 'sellOrders'
        ordering = ['-created_at']