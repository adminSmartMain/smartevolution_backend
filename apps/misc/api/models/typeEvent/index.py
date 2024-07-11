from django.db import models
from apps.base.models import BaseModel


class TypeEvent(BaseModel):
    code        = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'typeEvents'
        verbose_name = 'typeEvent'
        verbose_name_plural = 'typeEvents'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.description
