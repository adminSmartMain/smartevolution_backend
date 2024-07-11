from django.db import models
from apps.base.models import BaseModel


class PeriodRange(BaseModel):
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'periodRange'
        verbose_name = 'periodRange'
        verbose_name_plural = 'periodRanges'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.description
