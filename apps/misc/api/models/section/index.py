from django.db import models
from apps.base.models import BaseModel


class Section(BaseModel):
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'sections'
        verbose_name = 'section'
        verbose_name_plural = 'sections'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.description
