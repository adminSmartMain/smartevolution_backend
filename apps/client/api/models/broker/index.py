from django.db import models

# Relations
from apps.misc.models import City, TypeIdentity, Department
from apps.base.models import BaseModel

class Broker(BaseModel):
    type_identity   = models.ForeignKey(TypeIdentity, on_delete=models.CASCADE, blank=True)
    document_number = models.CharField(max_length=255, unique=True, error_messages={'unique': 'El número de documento ya existe'})
    first_name      = models.CharField(max_length=255, blank=True, null=True)
    last_name       = models.CharField(max_length=255, blank=True, null=True)
    social_reason   = models.CharField(max_length=255, blank=True, null=True)
    address         = models.CharField(max_length=255)
    email           = models.CharField(max_length=255, unique=True, error_messages={'unique': 'El correo electrónico ya existe'})
    phone_number    = models.CharField(max_length=255, unique=True, error_messages={'unique': 'El número de teléfono ya existe'})
    department      = models.ForeignKey(Department, on_delete=models.CASCADE, blank=True)
    city            = models.ForeignKey(City, on_delete=models.CASCADE, blank=True)

    class Meta:
        db_table = 'brokers'
        verbose_name = 'brokers'
        verbose_name_plural = 'brokers'
        ordering = ['-created_at']