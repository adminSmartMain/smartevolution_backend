from django.db import models

# Relations
from apps.base.models import BaseModel
from apps.client.api.models.index import Client


class Patrimony(BaseModel):
        payed_capital                   = models.FloatField()
        sup_capital_prima               = models.FloatField()
        legal_reserve                   = models.FloatField()
        periods_results                 = models.FloatField()
        accumulated_results             = models.FloatField()
        rev_patrimony_niif              = models.FloatField()
        total_patrimony                 = models.FloatField()
        passive_and_patrimony           = models.FloatField()
        total_assets_passives           = models.FloatField()

        class Meta:
                db_table = 'patrimony'
                verbose_name = 'patrimony'
                verbose_name_plural = 'patrimony'
                ordering = ['-created_at']