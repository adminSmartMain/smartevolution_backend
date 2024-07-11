from django.db import models
from apps.base.models import BaseModel


class Activity(BaseModel):

    description = models.TextField(blank=True)

    class Meta:
        db_table = 'activities'
        verbose_name = 'activity'
        verbose_name_plural = 'activities'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.description
