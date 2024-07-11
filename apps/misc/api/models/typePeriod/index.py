from django.db import models
from apps.base.models import BaseModel


class TypePeriod(BaseModel):
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'typePeriods'
        verbose_name = 'typePeriod'
        verbose_name_plural = 'typePeriods'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.description
