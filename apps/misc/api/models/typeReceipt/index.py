
from django.db import models
from apps.base.models import BaseModel


class TypeReceipt(BaseModel):
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'typeReceipt'
        verbose_name = 'typeReceipt'
        verbose_name_plural = 'typeReceipt'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.description
