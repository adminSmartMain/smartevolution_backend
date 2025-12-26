import logging
import uuid
from django.utils import timezone

from apps.bill.models import Bill, BillEvent
from apps.misc.api.models.typeEvent.index import TypeEvent
from apps.misc.api.models.typeBill.index import TypeBill

# ============================================================
# LOGGER
# ============================================================
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
console_handler.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(console_handler)

# ============================================================
# UUIDs FINALES
# ============================================================
UUID_FV = "fdb5feb4-24e9-41fc-9689-31aff60b76c9"
UUID_FV_TV = "a7c70741-8c1a-4485-8ed4-5297e54a978a"
UUID_RECHAZADA = "dcec6f03-5dc1-42ea-a525-afada28686da"
UUID_ENDOSADA = "29113618-6ab8-4633-aa8e-b3d6f242e8a4"

# ============================================================
# MAPEO EVENTOS DIAN → UUID INTERNO
# ============================================================
event_code_to_uuid = {
    '030': '07c61f28-83f8-4f91-b965-f685f86cf6bf',
    '031': '3d376019-618b-40eb-ae80-9cb143db54a4',
    '032': '141db270-23ec-49c1-87a7-352d5413d309',
    '033': 'c508eeb3-e0e8-48e8-a26f-5297f95c1f1f',
    '034': 'e76e9b7a-baeb-4972-b76e-3a8ce2d4fa30',
    '036': 'b8d4f8d3-aded-4b1f-873e-46c89a2538ed',
    '037': '3ea77762-7208-457a-b035-70069ee42b5e',
    '038': '0e333b6b-27b1-4aaf-87ce-ad60af6e52e6',
    '046': 'f5d475c0-4433-422f-b3d2-7964ea0aa5c4',
    '047': '3bb86c74-1d1c-4986-a905-a47624b09322',
}

# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================
def updateMassiveTypeBill(bills_queryset, billEvents_function):
    logger.debug("⚠⚠⚠ EJECUTANDO updateMassiveTypeBill ⚠⚠⚠")
    logger.debug(f"ARCHIVO: {__file__}")

    updated = 0
    errors = []

    logger.debug(f"TOTAL FACTURAS RECIBIDAS PARA PROCESAR: {len(bills_queryset)}")

    for bill in bills_queryset:
        logger.debug("--------------------------------------------------------")
        logger.debug(
            f"➡ Procesando factura ID {bill.id} | billId {bill.billId} | typeBill actual {bill.typeBill_id}"
        )

        # ❌ EXCLUIR ENDOSADAS
        if bill.typeBill_id == UUID_ENDOSADA:
            logger.warning(f"⛔ EXCLUIDA - Factura endosada. billId={bill.billId}")
            continue

        # ❌ EXCLUIR RECHAZADAS
        if bill.typeBill_id == UUID_RECHAZADA:
            logger.warning(f"⛔ EXCLUIDA - Factura rechazada. billId={bill.billId}")
            continue

        # ❌ EXCLUIR OPERACIONES CANCELADAS
        try:
            if hasattr(bill, "preoperation_set") and bill.preoperation_set.filter(status=4).exists():
                logger.warning(f"⛔ EXCLUIDA - Operación cancelada. billId={bill.billId}")
                continue
        except Exception as e:
            logger.error(f"❗ ERROR validando operaciones billId={bill.billId}: {e}")

        logger.info(f"✔ Factura PERMITIDA para actualización: billId={bill.billId}")

        try:
            # ----------------------------------------------------
            # FACTURA SIN CUFE → FV
            # ----------------------------------------------------
            if not bill.cufe:
                logger.info(f"ℹ Factura sin CUFE, asignando UUID_FV")

                if bill.typeBill_id != UUID_FV:
                    bill.typeBill_id = UUID_FV
                    bill.save(update_fields=["typeBill"])
                    updated += 1
                continue

            # ----------------------------------------------------
            # CONSULTAR EVENTOS DIAN
            # ----------------------------------------------------
            logger.debug(f"Consultando eventos DIAN para CUFE={bill.cufe}")
            result = billEvents_function(bill.cufe, update=True)

            new_type = result.get("type")
            api_events = result.get("events", [])
            logger.debug('dddd')
            logger.debug(api_events)
            current_owner = result.get("currentOwner", "").strip()

            fields_to_update = []

            # ----------------------------------------------------
            # ACTUALIZAR currentOwner
            # ----------------------------------------------------
            if hasattr(bill, "currentOwner"):
                if current_owner and current_owner != bill.currentOwner:
                    logger.info(
                        f"📝 Actualizando currentOwner: '{bill.currentOwner}' → '{current_owner}'"
                    )
                    bill.currentOwner = current_owner
                    fields_to_update.append("currentOwner")

            # ----------------------------------------------------
            # SINCRONIZAR EVENTOS (🔥 CLAVE 🔥)
            # ----------------------------------------------------
            if api_events:
                synced = sync_bill_events(bill, api_events)
                logger.info(f"📅 Eventos sincronizados: {synced}")

            # ----------------------------------------------------
            # ACTUALIZAR typeBill
            # ----------------------------------------------------
            if new_type and new_type != bill.typeBill_id:
                try:
                    TypeBill.objects.get(id=new_type)
                    bill.typeBill_id = new_type
                    fields_to_update.append("typeBill")
                    updated += 1
                except TypeBill.DoesNotExist:
                    logger.error(f"❗ typeBill {new_type} no existe")

            if fields_to_update:
                bill.save(update_fields=fields_to_update)

        except Exception as e:
            logger.error(f"❗ ERROR procesando billId={bill.billId}: {e}")
            errors.append({"billId": bill.billId, "error": str(e)})

    logger.error("========================================================")
    logger.error(f"🔥 TOTAL FACTURAS ACTUALIZADAS: {updated}")
    logger.error(f"❗ ERRORES: {len(errors)}")
    logger.error("========================================================")

    return {"updated": updated, "errors": errors}

# ============================================================
# SINCRONIZACIÓN DE EVENTOS (NO DUPLICA, NO ROMPE PK)
# ============================================================
def sync_bill_events(bill, api_events):
    """
    Sincroniza eventos DIAN:
    - Acepta event como CODE ('030') o UUID
    - NO duplica eventos
    - Usa (bill_id + event_id) como llave lógica
    """
    events_updated = 0

    # Eventos ya existentes en BD
    existing_events = {
        str(be.event_id): be
        for be in BillEvent.objects.filter(bill=bill)
    }

    for ev in api_events:
        raw_event = ev.get("event") or ev.get("code")
        date = ev.get("date")
   

        if not raw_event:
            continue

        # --------------------------------------------------
        # 1️⃣ Determinar UUID REAL del evento
        # --------------------------------------------------
        if raw_event in event_code_to_uuid:
            # viene como código DIAN (030, 032, etc)
            event_uuid = event_code_to_uuid[raw_event]
        else:
            # puede venir ya como UUID
            event_uuid = raw_event

        # --------------------------------------------------
        # 2️⃣ Validar UUID
        # --------------------------------------------------
        try:
            uuid.UUID(event_uuid)
        except ValueError:
            logger.warning(f"⚠ Evento DIAN inválido: {raw_event}")
            continue

        # --------------------------------------------------
        # 3️⃣ Si ya existe → actualizar
        # --------------------------------------------------
        if event_uuid in existing_events:
            be = existing_events[event_uuid]
            fields = []

            if date and be.date != date:
                be.date = date
                fields.append("date")

            

            if fields:
                be.updated_at = timezone.now()
                fields.append("updated_at")
                be.save(update_fields=fields)

            continue

        # --------------------------------------------------
        # 4️⃣ Crear nuevo evento
        # --------------------------------------------------
        try:
            type_event = TypeEvent.objects.get(id=event_uuid)
        except TypeEvent.DoesNotExist:
            logger.warning(f"⚠ TypeEvent {event_uuid} no existe en catálogo")
            continue

        BillEvent.objects.create(
            id=uuid.uuid4(),
            bill=bill,
            event=type_event,
            date=date,
            
            created_at=timezone.now(),
            updated_at=timezone.now(),
        )

        events_updated += 1

    return events_updated
