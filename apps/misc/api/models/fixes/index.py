from django.db import models
from apps.base.models import BaseModel
from apps.misc.api.models.index import Department

class Fixes(models.Model):

    id          = models.AutoField(primary_key=True)
    accountId   = models.CharField(max_length=255)
    date        = models.DateField()
    gmAmount    = models.FloatField()

    class Meta:
        db_table = 'fixes'
        verbose_name = 'fix'
        verbose_name_plural = 'fixes'
        ordering = ['accountId']
    