from django.db import models

# Relations
from apps.client.api.models.index import Client
from apps.base.models import BaseModel

class Request(BaseModel):
    client      = models.ForeignKey(Client, on_delete=models.CASCADE)
    status      = models.IntegerField(default=0)
    attended_by = models.ForeignKey('authentication.User', on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        db_table = 'requests'
        verbose_name = 'requests'
        verbose_name_plural = 'requests'
        ordering = ['-created_at']