from django.db import models
from apps.base.models import BaseModel
from apps.misc.models import TypeBill

class Bill(BaseModel):
    typeBill         = models.ForeignKey(TypeBill, on_delete=models.CASCADE)
    billId           = models.CharField(max_length=255,unique=False, error_messages={'unique': 'Ya existe una factura con este número'})
    emitterId        = models.CharField(max_length=255)
    emitterName      = models.CharField(max_length=255)
    payerId          = models.CharField(max_length=255)
    payerName        = models.CharField(max_length=255)
    billValue        = models.FloatField(default=0)
    subTotal         = models.FloatField(default=0)
    total            = models.FloatField(default=0)
    currentBalance   = models.FloatField(default=0)
    iva              = models.FloatField(default=0)
    dateBill         = models.CharField(max_length=255)
    datePayment      = models.CharField(max_length=255)
    cufe             = models.CharField(max_length=255, blank=True, null=True)
    expirationDate   = models.CharField(max_length=255)
    ret_fte          = models.FloatField(default=0)
    ret_ica          = models.FloatField(default=0)
    ret_iva          = models.FloatField(default=0)
    other_ret        = models.FloatField(default=0)
    creditNotesValue = models.FloatField(default=0)
    file             = models.TextField(blank=True, null=True)
    status           = models.SmallIntegerField(default=0)
    reBuyAvailable   = models.BooleanField(default=False)
    endorsed         = models.BooleanField(default=False)
    currentOwner     = models.CharField(max_length=255, blank=True, null=True)
    sameCurrentOwner = models.BooleanField(default=False)
    integrationCode  = models.CharField(max_length=255, blank=True, null=True)
    # Una factura puede existir localmente y quedar pendiente de sincronizar.
    billySyncStatus = models.CharField(max_length=20, default='synced')
    billyErrorCode = models.CharField(max_length=20, blank=True, null=True)
    billyErrorDetail = models.TextField(blank=True, null=True)
    billySyncAttempts = models.PositiveIntegerField(default=0)
    billyLastSyncAt = models.DateTimeField(blank=True, null=True)
    billyTokenScope = models.CharField(max_length=20, default='smart')
    billyEventsLastAttemptAt = models.DateTimeField(
    null=True,
    blank=True,
    )

    billyEventsLastSuccessAt = models.DateTimeField(
        null=True,
        blank=True,
    )

    billyEventsNextCheckAt = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
    )

    billyEventsConsecutiveErrors = models.PositiveIntegerField(
        default=0,
    )

    class Meta:
        db_table = 'bills'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=["emitterId"], name="idx_bill_emitter_id"),
        ]
