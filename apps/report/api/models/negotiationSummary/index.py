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
    manualAdjustment = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    observations     = models.TextField(blank=True)
    # Immutable COP settlement used by legal documents.  Legacy float columns
    # remain only to avoid modifying historic records.
    settledFutureValue = models.DecimalField(max_digits=18, decimal_places=0, null=True, blank=True)
    settledValueToDiscount = models.DecimalField(max_digits=18, decimal_places=0, null=True, blank=True)
    settledSMDiscount = models.DecimalField(max_digits=18, decimal_places=0, null=True, blank=True)
    settledInvestorValue = models.DecimalField(max_digits=18, decimal_places=0, null=True, blank=True)
    settledInvestorDiscount = models.DecimalField(max_digits=18, decimal_places=0, null=True, blank=True)
    settledCommissionValueBeforeTaxes = models.DecimalField(max_digits=18, decimal_places=0, null=True, blank=True)
    settledOperationValue = models.DecimalField(max_digits=18, decimal_places=0, null=True, blank=True)
    settledTableCommission = models.DecimalField(max_digits=18, decimal_places=0, null=True, blank=True)
    settledIva = models.DecimalField(max_digits=18, decimal_places=0, null=True, blank=True)
    settledRetIva = models.DecimalField(max_digits=18, decimal_places=0, null=True, blank=True)
    settledRetIca = models.DecimalField(max_digits=18, decimal_places=0, null=True, blank=True)
    settledRetFte = models.DecimalField(max_digits=18, decimal_places=0, null=True, blank=True)
    settledBillValue = models.DecimalField(max_digits=18, decimal_places=0, null=True, blank=True)
    settledTotalDiscounts = models.DecimalField(max_digits=18, decimal_places=0, null=True, blank=True)
    settledTotal = models.DecimalField(max_digits=18, decimal_places=0, null=True, blank=True)
    settledPendingToDeposit = models.DecimalField(max_digits=18, decimal_places=0, null=True, blank=True)
    settlementVersion = models.PositiveIntegerField(default=1)
    roundingPolicy = models.CharField(max_length=64, default='LARGEST_NOMINAL_HALF_UP_V1')
    settlementDimensions = models.JSONField(null=True, blank=True)


    class Meta:
        db_table = 'negotiationSummary'
        verbose_name = 'NegotiationSummary'
        verbose_name_plural = 'NegotiationSummaries'
        ordering = ['-created_at']
