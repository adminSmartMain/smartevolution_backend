from django.db import models

# Relations
from apps.base.models import BaseModel
from apps.client.api.models.index import Client


class Passives(BaseModel):
        financial_obligation_cp          = models.FloatField()
        providers                        = models.FloatField()
        unpaid_expenses                  = models.FloatField()
        unpaid_taxes                     = models.FloatField()
        linked_economics                 = models.FloatField()
        estimated_passives               = models.FloatField()
        current_liabilities              = models.FloatField()
        financial_obligation_lp          = models.FloatField()
        other_lp_leasing                 = models.FloatField()
        lp_passives                      = models.FloatField()
        total_passives                   = models.FloatField()

        class Meta:
                db_table = 'passives'
                verbose_name = 'passives'
                verbose_name_plural = 'passives'
                ordering = ['-created_at']