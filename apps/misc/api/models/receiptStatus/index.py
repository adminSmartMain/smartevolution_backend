from django.db import models
from apps.base.models import BaseModel


class ReceiptStatus(BaseModel):
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'receiptStatus'
        verbose_name = 'receiptStatus'
        verbose_name_plural = 'receiptStatus'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.description
