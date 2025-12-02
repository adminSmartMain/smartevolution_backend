import logging
import base64
from base64 import b64decode
from django.core.cache import cache
from rest_framework.exceptions import ValidationError
from apps.bill.models import Bill, CreditNote, BillEvent
from apps.misc.api.models.typeBill.index import TypeBill
# Configurar el logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Crear un handler de consola y definir el nivel
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Crear un formato para los mensajes de log
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Añadir el handler al logger
logger.addHandler(console_handler)
UUID_FV = "fdb5feb4-24e9-41fc-9689-31aff60b76c9"
UUID_FV_TV = "a7c70741-8c1a-4485-8ed4-5297e54a978a"
UUID_RECHAZADA = "dcec6f03-5dc1-42ea-a525-afada28686da"
UUID_ENDOSADA = "29113618-6ab8-4633-aa8e-b3d6f242e8a4"




def updateMassiveTypeBill(bills_queryset,billEvents):
    """
    Recalcula y actualiza el typeBill de cada factura del queryset
    usando la lógica correcta basada en eventos DIAN.
    """
    logger.error("⚠⚠⚠ EJECUTANDO updateMassiveTypeBill DESDE ESTE ARCHIVO ⚠⚠⚠")
    logger.error(f"ARCHIVO: {__file__}")
    updated = 0
    errors = []
    
    logger.debug(bills_queryset)

    for bill in bills_queryset:

        try:
            # Si no hay CUFE no podemos consultar eventos → marcar como FV
            if not bill.cufe:
                if bill.typeBill != UUID_FV:
                    bill.typeBill = UUID_FV
                    bill.save(update_fields=["typeBill"])
                    updated += 1
                continue

            # Obtener eventos desde tu función corregida
            result = billEvents(bill.cufe, update=False)
            logger.debug('SDASDFDSADSFDFSDGDFDSFGDSA')
            logger.debug(result)
            new_type = result.get("type")

            # Si hay diferencia, actualizamos
            if new_type and new_type != bill.typeBill_id:  
                try:
                    type_obj = TypeBill.objects.get(id=new_type)
                except TypeBill.DoesNotExist:
                    logger.error(f"⚠ typeBill {new_type} NO EXISTE — NO SE ACTUALIZA")
                    continue
                
                bill.typeBill = type_obj
                bill.save(update_fields=["typeBill"])
                updated += 1

        except Exception as e:
            errors.append({
                "billId": bill.billId,
                "error": str(e)
            })

    return {
        "updated": updated,
        "errors": errors
    }
