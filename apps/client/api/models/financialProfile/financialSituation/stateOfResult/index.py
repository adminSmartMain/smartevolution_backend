from django.db import models

# Relations
from apps.base.models import BaseModel
from apps.client.api.models.index import Client

class StateOfResult(BaseModel):
    gross_sale                            = models.FloatField()
    dtos_returns                          = models.FloatField()
    net_sales                             = models.FloatField()
    cost_of_sales                         = models.FloatField()
    gross_profit                          = models.FloatField()
    administrative_expenses_sales         = models.FloatField()
    dep_amortization                      = models.FloatField()
    operating_profit                      = models.FloatField()
    financial_income                      = models.FloatField()
    other_incomes                         = models.FloatField()
    financial_expenses                    = models.FloatField()
    other_expenditures                    = models.FloatField()
    income_before_taxes                   = models.FloatField()
    provision_for_taxes                   = models.FloatField()
    net_income                            = models.FloatField()

    class Meta:
        db_table = 'stateOfResult'
        verbose_name = 'stateOfResult'
        verbose_name_plural = 'stateOfResult'
        ordering = ['-created_at']