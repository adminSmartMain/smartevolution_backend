from django.db import models
from apps.base.models import BaseModel


class IntegrationHistory(BaseModel):
    integrationCode = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=255, null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    response = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'integrationHistory'
        verbose_name = 'integrationHistory'
        verbose_name_plural = 'integrationHistory'
        ordering = ['-created_at']
