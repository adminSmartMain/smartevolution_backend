from django.db             import models
from apps.base.models      import BaseModel
from apps.report.api.models.index    import SellOrder
from apps.operation.api.models.index import PreOperation

class SellOrderOperation(BaseModel):
    sellOrder    = models.ForeignKey(SellOrder, on_delete=models.CASCADE, related_name='sellOrderOperations')
    operation    = models.ForeignKey(PreOperation, on_delete=models.CASCADE, related_name='sellOrderOperations')
    
    class Meta:
        db_table = 'sellOrderOperation'
        verbose_name = 'sellOrderOperation'
        verbose_name_plural = 'sellOrderOperations'
        ordering = ['-created_at']