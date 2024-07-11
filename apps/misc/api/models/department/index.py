from django.db import models
from apps.base.models import BaseModel

class Department(BaseModel):
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'departments'
        verbose_name = 'department'
        verbose_name_plural = 'departments'
        ordering = ['description']
    
    def __str__(self) -> str:
        return self.description