
from django.db import models
from apps.base.models import BaseModel


class TypeOperation(BaseModel):
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'typeOperation'
        verbose_name = 'typeOperation'
        verbose_name_plural = 'typeOperations'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.description
