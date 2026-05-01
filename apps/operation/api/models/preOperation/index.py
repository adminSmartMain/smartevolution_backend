from django.db import models
from apps.base.models import BaseModel

# relations with other models
from apps.misc.models import TypeOperation
from apps.client.api.models.index import Client, Account, Broker
from apps.bill.api.models.index import Bill

class PreOperation(BaseModel):
    opId            = models.BigIntegerField()
    opType          = models.ForeignKey(TypeOperation, on_delete=models.CASCADE, error_messages={'required': 'El tipo de operación es requerido'})
    opDate          = models.DateField(error_messages={'required': 'La fecha de la operación es requerida'})
    applyGm         = models.BooleanField(default=False, blank=True, null=True)
    emitter         = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='preOperationsEmitter', error_messages={'required': 'El emisor es requerido'})
    payer           = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='preOperationsPayer', error_messages={'required': 'El pagador es requerido'})
    investor        = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='preOperationsInvestor', error_messages={'required': 'El inversionista es requerido'})
    clientAccount   = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='preOperationsInvestorAccount', error_messages={'required': 'La cuenta del inversionista es requerida'})
    bill            = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='preOperationsBill', error_messages={'required': 'La factura es requerida'})
    billFraction    = models.IntegerField(default=0, null=True, blank=True)
    DateBill        = models.DateField(error_messages={'required': 'La fecha de la factura es requerida'})
    DateExpiration  = models.DateField(error_messages={'required': 'La fecha de vencimiento es requerida'})
    probableDate    = models.DateField(error_messages={'required': 'La fecha probable es requerida'})
    opExpiration    = models.DateField(error_messages={'required': 'La fecha de vencimiento de la operación es requerida'})
    amount          = models.FloatField(default=0, error_messages={'required': 'El monto es requerido'})
    payedPercent    = models.FloatField(default=0, error_messages={'required': 'El porcentaje pagado es requerido'})
    payedAmount     = models.FloatField(default=0, error_messages={'required': 'El monto pagado es requerido'})
    opPendingAmount = models.FloatField(default=0, error_messages={'required': 'El monto pendiente de la operación es requerido'})
    discountTax     = models.FloatField(default=0, error_messages={'required': 'El descuento de impuestos es requerido'})
    investorTax     = models.FloatField(default=0, error_messages={'required': 'El impuesto del inversionista es requerido'})
    emitterBroker   = models.ForeignKey(Broker, on_delete=models.CASCADE, related_name='preOperationsEmitterBroker', error_messages={'required': 'El corredor del emisor es requerido'})
    investorBroker  = models.ForeignKey(Broker, on_delete=models.CASCADE, related_name='preOperationsInvestorBroker', error_messages={'required': 'El corredor del inversionista es requerido'})
    operationDays   = models.IntegerField(error_messages={'required': 'Los días de la operación es requerido'})
    presentValueInvestor = models.FloatField(default=0, error_messages={'required': 'El valor presente del inversionista es requerido'})
    presentValueSF       = models.FloatField(default=0, error_messages={'required': 'El valor presente del SF es requerido'})
    investorProfit       = models.FloatField(default=0, error_messages={'required': 'El beneficio del inversionista es requerido'})
    commissionSF         = models.FloatField(default=0, error_messages={'required': 'La comisión del SF es requerido'})
    GM                   = models.FloatField(default=0, error_messages={'required': 'La GM es requerido'})
    status               = models.IntegerField(default=0,)
    isRebuy              = models.BooleanField(default=False, blank=True, null=True)
    insufficientAccountBalance = models.BooleanField(default=False, blank=True, null=True)

    def __str__(self):
        return self.emitter.social_reason if self.emitter.social_reason else self.emitter.first_name + ' ' + self.emitter.last_name

    class Meta:
        db_table = 'operation'
        verbose_name = 'operation'
        verbose_name_plural = 'operations'
        ordering = ['-opDate','-opId']
        
        

class OperationLog(BaseModel):
    STATUS_CHOICES = (
        ("SUCCESS", "Success"),
        ("ERROR", "Error"),
        ("PARTIAL", "Partial"),
        ("INFO", "Info"),
    )

    SOURCE_CHOICES = (
        ("SINGLE", "Single Operation"),
        ("BULK", "Bulk Operation"),
        ("UPLOAD_EXCEL", "Upload Excel"),
        ("REGISTER_FROM_UPLOAD", "Register From Upload"),
        ("PATCH", "Patch Operation"),
        ("DELETE", "Delete Operation"),
        ("BILL", "Bill"),
    )

    opId = models.BigIntegerField(null=True, blank=True)

    pre_operation = models.ForeignKey(
        "operation.PreOperation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logs"
    )

    source = models.CharField(max_length=40, choices=SOURCE_CHOICES)
    action = models.CharField(max_length=120)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="INFO")

    message = models.TextField()
    error_type = models.CharField(max_length=255, null=True, blank=True)
    error_detail = models.TextField(null=True, blank=True)
    stack_trace = models.TextField(null=True, blank=True)

    row_index = models.IntegerField(null=True, blank=True)
    bill_code = models.CharField(max_length=255, null=True, blank=True)
    bill_id_ref = models.CharField(max_length=255, null=True, blank=True)

    request_payload = models.JSONField(null=True, blank=True)
    response_payload = models.JSONField(null=True, blank=True)
    extra_data = models.JSONField(null=True, blank=True)

    user_email = models.CharField(max_length=255, null=True, blank=True)
    user_id_ref = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "operation_log"
        verbose_name = "operation log"
        verbose_name_plural = "operation logs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.source} - {self.action} - {self.status} - opId:{self.opId or 'N/A'}"
    
    
    
class MassiveOperationDraft(BaseModel):
    STATUS_DRAFT = "DRAFT"
    STATUS_READY_FOR_EXCEL = "READY_FOR_EXCEL"
    STATUS_REGISTERED = "REGISTERED"
    STATUS_CANCELLED = "CANCELLED"

    STATUS_CHOICES = (
        (STATUS_DRAFT, "Borrador"),
        (STATUS_READY_FOR_EXCEL, "Listo para Excel"),
        (STATUS_REGISTERED, "Registrado"),
        (STATUS_CANCELLED, "Cancelado"),
    )

    opId = models.BigIntegerField(null=True, blank=True)
    opDate = models.DateField(null=True, blank=True)
    opType = models.ForeignKey(TypeOperation, null=True, blank=True, on_delete=models.SET_NULL)

    emitter = models.ForeignKey(Client, null=True, blank=True, on_delete=models.SET_NULL, related_name="massive_drafts_emitter")
    payer = models.ForeignKey(Client, null=True, blank=True, on_delete=models.SET_NULL, related_name="massive_drafts_payer")
    emitterBroker = models.ForeignKey(Broker, null=True, blank=True, on_delete=models.SET_NULL)

    currentStep = models.IntegerField(default=0)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_DRAFT)

    selectedBills = models.JSONField(default=list, blank=True)
    investorAssignments = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    registeredOpId = models.BigIntegerField(null=True, blank=True)
    expiresAt = models.DateTimeField(null=True, blank=True)
    class Meta:
        indexes = [
            models.Index(
                fields=[
                    "state",
                    "user_created_at",
                    "status",
                    "-updated_at",
                    "-created_at",
                ],
                name="massive_draft_list_idx",
            ),
        ]