from django.db import models
from apps.base.models import BaseModel


class TypeExpenditure(BaseModel):
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'typeExpenditures'
        verbose_name = 'typeExpenditure'
        verbose_name_plural = 'typeExpenditures'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.description
