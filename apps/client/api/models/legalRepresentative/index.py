from django.db import models

# Relations
from apps.client.api.models.index import Client
from apps.misc.api.models.index import TypeIdentity, City, Country, Department
from apps.base.models import BaseModel

class LegalRepresentative(BaseModel):
    client          = models.ForeignKey(Client, on_delete=models.CASCADE)
    type_identity   = models.ForeignKey(TypeIdentity, on_delete=models.CASCADE)
    document_number = models.CharField(max_length=255)
    first_name      = models.CharField(max_length=255, null=True)
    last_name       = models.CharField(max_length=255, null=True)
    social_reason   = models.CharField(max_length=255, null=True)
    birth_date      = models.DateField(null=True)
    department      = models.ForeignKey(Department, on_delete=models.CASCADE, blank=True, null=True)
    city            = models.ForeignKey(City, on_delete=models.CASCADE, blank=True, null=True)
    citizenship     = models.ForeignKey(Country, on_delete=models.CASCADE, blank=True, null=True)
    address         = models.CharField(max_length=255)
    phone_number    = models.CharField(max_length=255 , unique=False)
    email           = models.EmailField(max_length=255)
    position        = models.CharField(max_length=255)


    class Meta:
        db_table = 'legalRepresentatives'
        verbose_name = 'legalRepresentatives'
        verbose_name_plural = 'legalRepresentatives'
        ordering = ['-created_at']