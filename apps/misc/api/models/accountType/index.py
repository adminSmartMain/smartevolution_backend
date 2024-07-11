from django.db import models
from apps.base.models import BaseModel


class AccountType(BaseModel):
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'accountTypes'
        verbose_name = 'accountType'
        verbose_name_plural = 'accountTypes'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.description
