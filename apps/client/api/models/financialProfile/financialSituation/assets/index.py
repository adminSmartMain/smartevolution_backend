from django.db import models

# Relations
from apps.base.models import BaseModel
from apps.client.api.models.index import Client


class Assets(BaseModel):
        cash_and_investments            = models.FloatField()
        clients_wallet                  = models.FloatField()
        cxc_partners                    = models.FloatField()
        other_cxc                       = models.FloatField()
        net_cxc                         = models.FloatField()
        raw_material_and_others         = models.FloatField()
        products_finished               = models.FloatField()
        total_inventory                 = models.FloatField()
        advances_and_progress           = models.FloatField()
        current_assets                  = models.FloatField()
        lands_and_buildings             = models.FloatField()
        m_and_e_vehicles                = models.FloatField()
        gross_fixed_assets              = models.FloatField()
        dep_acum                        = models.FloatField()
        net_fixed_assets                = models.FloatField()
        difer_intang_leasing            = models.FloatField()
        investments_and_others          = models.FloatField()
        total_other_assets              = models.FloatField()
        total_assets                    = models.FloatField()


        class Meta:
            db_table = 'assets'
            verbose_name = 'assets'
            verbose_name_plural = 'assets'
            ordering = ['-created_at']