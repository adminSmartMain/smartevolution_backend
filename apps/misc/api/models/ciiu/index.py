from django.db import models
from apps.base.models import BaseModel

# Models
from ..index import Section, Activity


class CIIU(BaseModel):
    section     = models.ForeignKey(Section, on_delete=models.CASCADE, blank=True)
    activity    = models.ForeignKey(Activity, on_delete=models.CASCADE, blank=True)
    code        = models.CharField(blank=True, max_length=255, unique=True)

    class Meta:
        db_table = 'ciiu'
        verbose_name = 'ciiu'
        verbose_name_plural = 'ciiu'
        ordering = ['-created_at']
    
    def __str__(self) -> str:
        return self.code + ' - ' + self.section.description + ' - ' + self.activity.description