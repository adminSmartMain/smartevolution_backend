from django.db import models

# Relations
from apps.client.api.models.index import Client
from apps.base.models import BaseModel

class Contact(BaseModel):
    client        = models.ForeignKey(Client, on_delete=models.CASCADE)
    first_name    = models.CharField(max_length=255, null=True)
    last_name     = models.CharField(max_length=255, null=True)
    social_reason = models.CharField(max_length=255, null=True)
    phone_number  = models.CharField(max_length=255)
    email         = models.EmailField(max_length=255)
    position      = models.CharField(max_length=255, null=True)

    class Meta:
        db_table = 'Contacts'
        verbose_name = 'Contacts'
        verbose_name_plural = 'Contacts'
        ordering = ['-created_at']


    def __str__(self):
        if self.client.social_reason != None:
            return self.client.social_reason + ' ' + self.first_name + ' ' + self.last_name
        else:
            return self.client.first_name + ' '+ self.client.last_name + ' - ' + self.first_name + ' ' + self.last_name