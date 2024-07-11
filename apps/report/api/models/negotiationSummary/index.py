from django.db import models
from apps.base.models import BaseModel


class NegotiationSummary(BaseModel):
    
    opId        = models.CharField(max_length=255, blank=False, error_messages={'required': 'Operación requerida'})
    date        = models.DateField(blank=False,error_messages={'required': 'Fecha requerida'})
    emitter     = models.CharField(max_length=255 ,blank=False, error_messages={'required': 'Emisor requerido'})
    payer       = models.CharField(max_length=255, blank=False,error_messages={'required': 'Pagador requerido'})
    emitterId   = models.CharField(max_length=255, blank=False,error_messages={'required': 'Emisor requerido'})
    payerId     = models.CharField(max_length=255, blank=False,error_messages={'required': 'Pagador requerido'})
    futureValue = models.FloatField(default=0)
    payedPercent = models.CharField(max_length=255, blank=False,error_messages={'required': 'Porcentaje pagado requerido'})
    valueToDiscount = models.FloatField(default=0)
    discountTax = models.FloatField(default=0)
    discountedDays = models.CharField(max_length=255, blank=False,error_messages={'required': 'Porcentaje pagado requerido'})
    SMDiscount = models.FloatField(default=0)
    investorValue = models.FloatField(default=0)
    investorDiscount = models.FloatField(default=0)
    commissionValueBeforeTaxes = models.FloatField(default=0)
    operationValue = models.FloatField(default=0)
    tableCommission = models.FloatField(default=0)
    iva = models.FloatField(default=0)
    retIva = models.FloatField(default=0)
    retIca = models.FloatField(default=0)
    retFte = models.FloatField(default=0)
    billId = models.CharField(max_length=255, blank=False, error_messages={'required': 'Factura requerida'})
    billValue = models.FloatField(default=0)
    totalDiscounts = models.FloatField(default=0)
    totalDeposits  = models.FloatField(default=0)
    total     = models.FloatField(default=0)
    pendingToDeposit = models.FloatField(default=0)
    observations     = models.TextField(blank=True)


    class Meta:
        db_table = 'negotiationSummary'
        verbose_name = 'NegotiationSummary'
        verbose_name_plural = 'NegotiationSummaries'
        ordering = ['-created_at']