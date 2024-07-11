from django.db import models
from apps.base.models import BaseModel
from apps.misc.api.models.index import Department

class City(BaseModel):

    description = models.TextField(blank=True)
    department  = models.ForeignKey(Department, on_delete=models.CASCADE, blank=True)

    class Meta:
        db_table = 'cities'
        verbose_name = 'city'
        verbose_name_plural = 'cities'
        ordering = ['description']
    
    def __str__(self) -> str:
        return self.description + ' - ' + self.department.description