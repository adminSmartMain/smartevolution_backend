from django.db import models

# Relations
from apps.misc.models import City, TypeIdentity, TypeCLient, CIIU, Country, Department, AccountType
from apps.client.api.models.broker.index import Broker
from apps.base.models import BaseModel


class Client(BaseModel):
    type_client     = models.ForeignKey(TypeCLient, on_delete=models.CASCADE, error_messages={'required': 'El tipo de cliente es requerido'})
    type_identity   = models.ForeignKey(TypeIdentity, on_delete=models.CASCADE, error_messages={'required': 'El tipo de identificación es requerido'})
    document_number = models.CharField(max_length=255, error_messages={'required': 'El número de identificación es requerido'})
    first_name      = models.CharField(max_length=255, null=True,blank=True)
    last_name       = models.CharField(max_length=255, null=True,blank=True)
    social_reason   = models.CharField(max_length=255, null=True,blank=True)
    birth_date      = models.DateField(null=True,blank=True)
    department      = models.ForeignKey(Department, on_delete=models.CASCADE, null=True)
    city            = models.ForeignKey(City, on_delete=models.CASCADE, null=True)
    citizenship     = models.ForeignKey(Country, on_delete=models.CASCADE, null=True,blank=True)
    address         = models.CharField(max_length=255)
    email           = models.CharField(max_length=255, unique=False)
    phone_number    = models.CharField(max_length=255, unique=False)
    ciiu            = models.ForeignKey(CIIU, on_delete=models.CASCADE, null=True,blank=True)
    broker          = models.ForeignKey(Broker, on_delete=models.CASCADE, null=True, blank=True)
    user            = models.ForeignKey('authentication.User', on_delete=models.CASCADE, null=True, blank=True)
    income          = models.SmallIntegerField(default=0)
    entered_by      = models.ForeignKey('authentication.User', on_delete=models.CASCADE, related_name='entered_by')
    status          = models.IntegerField(default=0)

    class Meta:
        db_table = 'clients'
        verbose_name = 'clients'
        verbose_name_plural = 'clients'
        ordering = ['-created_at']
