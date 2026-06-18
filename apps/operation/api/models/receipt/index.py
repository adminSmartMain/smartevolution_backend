from django.db import models
from apps.base.models import BaseModel

# Relations
from apps.client.api.models.index import Account
from apps.operation.api.models.index import PreOperation
from apps.misc.models import TypeReceipt, ReceiptStatus


class ReceiptImportSession(BaseModel):
    """
    Sesión técnica de importación/registro masivo.
    No representa un lote financiero; solo agrupa recaudos para auditoría.
    """

    SOURCE_CHOICES = [
        ("manual", "Manual"),
        ("excel", "Excel"),
        ("massive", "Masivo"),
    ]

    source = models.CharField(max_length=30, default="excel", choices=SOURCE_CHOICES)
    fileName = models.CharField(max_length=255, null=True, blank=True)
    applicationDate = models.DateField(null=True, blank=True)
    receiptStatus = models.ForeignKey(
        ReceiptStatus,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    totalRows = models.IntegerField(default=0)
    processedRows = models.IntegerField(default=0)
    createdCount = models.IntegerField(default=0)
    errorCount = models.IntegerField(default=0)
    createdBy = models.ForeignKey(
        "authentication.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="receipt_import_sessions",
    )
    notes = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "receipt_import_sessions"
        verbose_name = "Receipt Import Session"
        verbose_name_plural = "Receipt Import Sessions"
        ordering = ["-created_at"]


class Receipt(BaseModel):
    CONTROL_ACTIVE = "ACTIVE"
    CONTROL_VOIDED = "VOIDED"
    CONTROL_ADJUSTED = "ADJUSTED"

    CONTROL_STATUS_CHOICES = [
        (CONTROL_ACTIVE, "Activo"),
        (CONTROL_VOIDED, "Anulado"),
        (CONTROL_ADJUSTED, "Ajustado"),
    ]

    dId                      = models.IntegerField(default=0)
    date                     = models.DateField()
    operation                = models.ForeignKey(PreOperation, on_delete=models.CASCADE, related_name="receipts")
    typeReceipt              = models.ForeignKey(TypeReceipt, on_delete=models.CASCADE)
    receiptStatus            = models.ForeignKey(ReceiptStatus, on_delete=models.CASCADE, blank=True, null=True)
    account                  = models.ForeignKey(Account, on_delete=models.CASCADE, blank=True, null=True, related_name="receipts")
    realDays                 = models.IntegerField(default=0)
    additionalDays           = models.IntegerField(default=0)
    calculatedDays           = models.IntegerField(default=0)
    additionalInterests      = models.FloatField(default=0)
    additionalInterestsSM    = models.FloatField(default=0)
    investorInterests        = models.FloatField(default=0)
    tableInterests           = models.FloatField(default=0)
    futureValueRecalculation = models.FloatField(default=0)
    tableRemaining           = models.FloatField(default=0)
    remaining                = models.FloatField(default=0)
    payedAmount              = models.FloatField(default=0)
    presentValueInvestor     = models.FloatField(default=0)

    # Control de anulación / ajuste.
    controlStatus = models.CharField(
        max_length=30,
        default=CONTROL_ACTIVE,
        choices=CONTROL_STATUS_CHOICES,
    )
    originalReceipt = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="corrections",
    )
    replacedBy = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="replaces",
    )
    voidReason = models.TextField(null=True, blank=True)
    voidedAt = models.DateTimeField(null=True, blank=True)
    voidedBy = models.ForeignKey(
        "authentication.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="voided_receipts",
    )
    adjustmentReason = models.TextField(null=True, blank=True)
    importSession = models.ForeignKey(
        ReceiptImportSession,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="receipts",
    )

    def __str__(self):
        try:
            return self.operation.bill.billId
        except Exception:
            return str(self.id)

    class Meta:
        db_table = "receipts"
        verbose_name = "Receipt"
        verbose_name_plural = "Receipts"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["operation", "state"], name="idx_receipt_operation_state"),
            models.Index(fields=["operation", "date", "created_at"], name="idx_receipt_operation_order"),
            models.Index(fields=["controlStatus"], name="idx_receipt_control_status"),
            models.Index(fields=["date"], name="idx_receipt_date"),
        ]


class ReceiptSnapshot(BaseModel):
    """Foto contable antes y después de crear un recaudo."""

    receipt = models.OneToOneField(
        Receipt,
        on_delete=models.CASCADE,
        related_name="snapshot",
    )

    # Operación antes del recaudo.
    operationStatusBefore = models.IntegerField(null=True, blank=True)
    operationPendingBefore = models.FloatField(null=True, blank=True)
    operationAmountBefore = models.FloatField(null=True, blank=True)
    operationPayedAmountBefore = models.FloatField(null=True, blank=True)

    # Cuenta antes del recaudo.
    accountBalanceBefore = models.FloatField(null=True, blank=True)

    # Factura antes del recaudo.
    billCurrentBalanceBefore = models.FloatField(null=True, blank=True)
    billReBuyAvailableBefore = models.BooleanField(null=True, blank=True)

    # Operación después del recaudo.
    operationStatusAfter = models.IntegerField(null=True, blank=True)
    operationPendingAfter = models.FloatField(null=True, blank=True)
    operationAmountAfter = models.FloatField(null=True, blank=True)
    operationPayedAmountAfter = models.FloatField(null=True, blank=True)

    # Cuenta después del recaudo.
    accountBalanceAfter = models.FloatField(null=True, blank=True)

    # Factura después del recaudo.
    billCurrentBalanceAfter = models.FloatField(null=True, blank=True)
    billReBuyAvailableAfter = models.BooleanField(null=True, blank=True)

    class Meta:
        db_table = "receipt_snapshots"
        verbose_name = "Receipt Snapshot"
        verbose_name_plural = "Receipt Snapshots"
        indexes = [
            models.Index(fields=["receipt"], name="idx_snapshot_receipt"),
        ]
