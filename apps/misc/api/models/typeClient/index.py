from django.db import models
from apps.base.models import BaseModel

class TypeCLient(BaseModel):
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'typeClients'
        verbose_name = 'typeClient'
        verbose_name_plural = 'typeClients'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.description