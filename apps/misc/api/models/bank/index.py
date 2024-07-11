from django.db import models
from apps.base.models import BaseModel


class Bank(BaseModel):
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'banks'
        verbose_name = 'bank'
        verbose_name_plural = 'banks'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.description
