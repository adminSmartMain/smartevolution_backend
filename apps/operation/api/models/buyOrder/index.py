from django.db import models
from apps.base.models import BaseModel

# relations with other models
from apps.operation.api.models.index import PreOperation


class BuyOrder(BaseModel):
    operation   = models.ForeignKey(PreOperation, on_delete=models.CASCADE)
    code        = models.CharField(max_length=255, blank=True, null=True)
    name        = models.CharField(max_length=255, blank=True, null=True)
    url         = models.CharField(max_length=255, blank=True, null=True)
    date        = models.DateField(blank=True, null=True)
    status      = models.IntegerField(default=0)
    signStatus  = models.IntegerField(default=0)

    class Meta:
        db_table = 'buyOrder'
        verbose_name = 'BuyOrder'
        verbose_name_plural = 'BuyOrders'
        ordering = ['-date']