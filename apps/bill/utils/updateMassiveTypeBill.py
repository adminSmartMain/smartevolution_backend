import logging
from apps.bill.models import Bill, BillEvent
from apps.misc.api.models.typeEvent.index import TypeEvent
from apps.misc.api.models.typeBill.index import TypeBill
from django.utils import timezone
import uuid
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
# UUIDs finales
UUID_FV = "fdb5feb4-24e9-41fc-9689-31aff60b76c9"
UUID_FV_TV = "a7c70741-8c1a-4485-8ed4-5297e54a978a"
UUID_RECHAZADA = "dcec6f03-5dc1-42ea-a525-afada28686da"
UUID_ENDOSADA = "29113618-6ab8-4633-aa8e-b3d6f242e8a4"

def updateMassiveTypeBill(bills_queryset, billEvents_function):
    """
    Recalcula y actualiza el typeBill, eventos y currentOwner de las facturas PERMITIDAS.
    Excluye:
      - Facturas endosadas
      - Facturas rechazadas
      - Facturas con operaciones canceladas (status = 4)
    """
    logger.error("⚠⚠⚠ EJECUTANDO updateMassiveTypeBill ⚠⚠⚠")
    logger.error(f"ARCHIVO: {__file__}")
    updated = 0
    errors = []

    logger.debug(f"TOTAL FACTURAS RECIBIDAS PARA PROCESAR: {len(bills_queryset)}")

    for bill in bills_queryset:
        logger.debug("--------------------------------------------------------")
        logger.debug(f"➡ Procesando factura ID {bill.id} | billId {bill.billId} | typeBill actual {bill.typeBill_id}")

        # 1) ❌ EXCLUIR ENDOSADAS
        if bill.typeBill_id == UUID_ENDOSADA:
            logger.warning(f"⛔ EXCLUIDA - Factura endosada (UUID_ENDOSADA). billId={bill.billId}")
            continue

        # 2) ❌ EXCLUIR RECHAZADAS
        if bill.typeBill_id == UUID_RECHAZADA:
            logger.warning(f"⛔ EXCLUIDA - Factura rechazada (UUID_RECHAZADA). billId={bill.billId}")
            continue

        # 3) ❌ EXCLUIR FACTURAS CON OPERACIÓN CANCELADA
        try:
            if hasattr(bill, "preoperation_set") and bill.preoperation_set.filter(status=4).exists():
                logger.warning(f"⛔ EXCLUIDA - Operación cancelada (status 4). billId={bill.billId}")
                continue
        except Exception as e:
            logger.error(f"❗ ERROR verificando operaciones canceladas para billId={bill.billId}: {str(e)}")

        # ------------------------------------------------------------
        # SI LLEGA AQUÍ → LA FACTURA **SÍ CUMPLE LAS REGLAS**
        logger.info(f"✔ Factura PERMITIDA para actualización: billId={bill.billId}")
        # ------------------------------------------------------------

        try:
            # Si no hay CUFE → marcar como FV
            if not bill.cufe:
                logger.info(f"ℹ Factura sin CUFE, asignando tipo UUID_FV. billId={bill.billId}")

                if bill.typeBill != UUID_FV:
                    bill.typeBill = UUID_FV
                    bill.save(update_fields=["typeBill"])
                    updated += 1
                    logger.info(f"   ✔ Actualizada → Nuevo typeBill UUID_FV. billId={bill.billId}")
                else:
                    logger.info("   (sin cambios)")
                continue

            # Obtener eventos desde la API de Billy
            logger.debug(f"Consultando eventos DIAN para CUFE={bill.cufe}")
            result = billEvents_function(bill.cufe, update=True)  # update=True para incluir eventos de endoso

            logger.debug(f"Respuesta eventos: {result}")

            new_type = result.get("type")
            api_events = result.get("events", [])
            current_owner = result.get("currentOwner", "").strip()

            # Inicializar lista de campos a actualizar
            fields_to_update = []
            
            # Actualizar currentOwner en el modelo Bill si existe el campo
            if hasattr(bill, 'currentOwner'):
                if current_owner and current_owner != bill.currentOwner:
                    logger.info(f"   📝 Actualizando currentOwner: '{bill.currentOwner}' → '{current_owner}'")
                    bill.currentOwner = current_owner
                    fields_to_update.append("currentOwner")
                else:
                    logger.debug(f"   currentOwner sin cambios: '{bill.currentOwner}'")

            # Sincronizar eventos en la base de datos (similar al serializer)
            if api_events:
                events_updated = sync_bill_events(bill, api_events)
                logger.info(f"   📅 Eventos sincronizados: {events_updated} registros")
            else:
                logger.debug("   No hay eventos para sincronizar")

            # Actualizar typeBill si ha cambiado
            type_changed = False
            if new_type and new_type != bill.typeBill_id:
                logger.info(
                    f"🔄 Actualizando typeBill billId={bill.billId} | {bill.typeBill_id} → {new_type}"
                )

                try:
                    type_obj = TypeBill.objects.get(id=new_type)
                    bill.typeBill = type_obj
                    fields_to_update.append("typeBill")
                    type_changed = True
                    updated += 1
                    
                except TypeBill.DoesNotExist:
                    logger.error(f"❗ typeBill {new_type} NO EXISTE — no se actualiza billId={bill.billId}")
                    continue
            else:
                logger.info("   (sin cambios en typeBill)")

            # Guardar todos los cambios acumulados
            if fields_to_update:
                bill.save(update_fields=fields_to_update)
                if type_changed:
                    logger.info(f"   ✔ Actualizada correctamente (typeBill y currentOwner)")
                else:
                    logger.info(f"   ✔ Actualizado solo currentOwner")

        except Exception as e:
            logger.error(f"❗ ERROR procesando billId={bill.billId}: {str(e)}")
            errors.append({"billId": bill.billId, "error": str(e)})

    logger.error("========================================================")
    logger.error(f"   🔥 TOTAL FACTURAS ACTUALIZADAS: {updated}")
    logger.error(f"   ❗ ERRORES: {len(errors)}")
    logger.error("========================================================")

    return {
        "updated": updated,
        "errors": errors
    }


def sync_bill_events(bill, api_events):
    events_updated = 0
    
    for ev in api_events:
        event_uuid = ev.get('event')  # <-- YA NO PISAMOS EL MÓDULO uuid
        date = ev.get('date')
        description = ev.get('description', '')
      
        if not event_uuid:
            continue
            
        try:
            type_ev = TypeEvent.objects.get(id=event_uuid)
        except TypeEvent.DoesNotExist:
            logger.warning(f"❗ Tipo de evento {event_uuid} no existe para bill {bill.billId}")
            continue

        defaults = {
            'date': date, 
            'updated_at': timezone.now()
        }

        if description and hasattr(BillEvent, 'description'):
            defaults['description'] = description

        bill_ev, created = BillEvent.objects.update_or_create(
          
            bill=bill,
            event=type_ev,
            defaults=defaults
        )

        events_updated += 1
        
    return events_updated
