from django.db import models
from apps.base.models import BaseModel


class Role(BaseModel):
    
    description = models.TextField(blank=False, null=False)

    def __str__(self):
        return self.description

    class Meta:
        db_table = 'roles'
        verbose_name = 'role'
        verbose_name_plural = 'roles'
        ordering = ['-created_at']
