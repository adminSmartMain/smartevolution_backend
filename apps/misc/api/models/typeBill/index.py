from django.db import models
from apps.base.models import BaseModel


class TypeBill(BaseModel):
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'typeBill'
        verbose_name = 'typeBill'
        verbose_name_plural = 'typeBill'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.description
