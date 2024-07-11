from enum import unique
from django.db import models

# Relations
from apps.client.api.models.index import Client
from apps.base.models import BaseModel
from apps.misc.models import TypePeriod, PeriodRange
from .financialSituation.index import Assets, Passives, Patrimony, StateOfResult


class FinancialProfile(BaseModel):
    period                      = models.IntegerField()
    typePeriod                  = models.ForeignKey(TypePeriod, on_delete=models.CASCADE)
    client                      = models.ForeignKey(Client, on_delete=models.CASCADE)
    periodRange                 = models.ForeignKey(PeriodRange, on_delete=models.CASCADE, null=True, blank=True)
    periodDays                  = models.IntegerField(default=0, null=True, blank=True)
    periodStartDate             = models.DateField(null=True, blank=True)
    periodEndDate               = models.DateField(null=True, blank=True)
    balance                     = models.FileField(upload_to='financialProfile/balance/')
    stateOfCashflow             = models.FileField(upload_to='financialProfile/stateOfCashflow/')
    financialStatementAudit     = models.FileField(upload_to='financialProfile/financialStatementAudit/')
    managementReport            = models.FileField(upload_to='financialProfile/managementReport/')
    certificateOfStockOwnership = models.FileField(upload_to='financialProfile/certificateOfStockOwnership/')
    rentDeclaration             = models.FileField(upload_to='financialProfile/rentDeclaration/')
    assets                      = models.ForeignKey(Assets, on_delete=models.CASCADE, blank=True)
    passives                    = models.ForeignKey(Passives, on_delete=models.CASCADE, blank=True)
    patrimony                   = models.ForeignKey(Patrimony, on_delete=models.CASCADE, blank=True)
    stateOfResult               = models.ForeignKey(StateOfResult, on_delete=models.CASCADE, blank=True)

    class Meta:
        db_table = 'FinancialProfiles'
        verbose_name = 'FinancialProfiles'
        verbose_name_plural = 'FinancialProfiles'
        ordering = ['-created_at']