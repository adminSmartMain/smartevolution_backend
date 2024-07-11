
from django.db import models
from apps.base.models import BaseModel


class TypeIdentity(BaseModel):
    description  = models.TextField(blank=True)
    abbreviation = models.CharField(max_length=10, blank=True)
    class Meta:
        db_table = 'typeIdentities'
        verbose_name = 'typeIdentity'
        verbose_name_plural = 'typeIdentities'
        ordering = ['-created_at']
    
    def __str__(self) -> str:
        return self.description