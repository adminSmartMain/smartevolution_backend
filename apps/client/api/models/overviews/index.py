from django.db import models

# Relations
from apps.client.api.models.index import Client
from apps.base.models import BaseModel


class Overview(BaseModel):
    client              = models.ForeignKey(Client, on_delete=models.CASCADE)
    qualitativeOverview = models.TextField()
    financialAnalisis   = models.TextField()

    class Meta:
        db_table = 'Overviews'
        verbose_name = 'Overviews'
        verbose_name_plural = 'Overviews'
        ordering = ['-created_at']