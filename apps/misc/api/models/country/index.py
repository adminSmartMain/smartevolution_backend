from django.db import models
from apps.base.models import BaseModel


class Country(BaseModel):

    name_en   = models.CharField(max_length=100, blank=True)
    name_es   = models.CharField(max_length=100, blank=True)
    dial_code = models.CharField(max_length=10, blank=True)
    code      = models.CharField(max_length=10, blank=True)
    src       = models.CharField(max_length=100, blank=True)
    srcSet    = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'countries'
        verbose_name = 'country'
        verbose_name_plural = 'countries'
        ordering = ['-created_at']
    
    def __str__(self) -> str:
        return self.description