import logging
import uuid
import re
from django.db import transaction
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

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
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
# CÓDIGOS DE EVENTOS PARA CLASIFICACIÓN RADIAN
# ============================================================
RECHAZO_CODES = {"031"}          # reclamo
ENDOSO_CODES = {"037", "047"}    # endoso electrónico (ajusta si manejas otros)
TV_REQUIRED = {"030", "032"}     # recibido + bien/servicio
TV_ACCEPT = {"033", "034"}       # aceptación expresa (o 034)

# ============================================================
# HELPERS
# ============================================================
def normalize_description(text: str) -> str:
    if not text:
        return ""
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def is_valid_uuid(val: str) -> bool:
    try:
        uuid.UUID(str(val))
        return True
    except Exception:
        return False


def compute_type_bill_from_events(api_events):
    """
    Reglas:
    - Rechazada: si tiene 031
    - Endosada: si tiene 037 o 047
    - FV-TV: si tiene 030 y 032 y (033 o 034)
    - FV: en otro caso
    """
    codes = {(e.get("code") or "").strip() for e in (api_events or [])}
    codes.discard("")

    if codes & RECHAZO_CODES:
        return UUID_RECHAZADA

    if codes & ENDOSO_CODES:
        return UUID_ENDOSADA

    if (TV_REQUIRED <= codes) and (codes & TV_ACCEPT):
        return UUID_FV_TV

    return UUID_FV


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================
@transaction.atomic
def updateMassiveTypeBill(bills_queryset, billEvents_function):
    """
    Recalcula typeBill y sincroniza BillEvents.

    billEvents_function(cufe, update=True) DEBE devolver:
    {
        "events": [
            {
              "code": "036",
              "dianDescription": "...",   # ideal
              "description": "...",       # opcional
              "supplierDescription": "...",
              "date": "YYYY-MM-DDTHH:mm:ss" o "YYYY-MM-DD",
              ...
            },
            ...
        ],
        "currentOwner": "...",
        ...
    }
    """
    logger.debug("⚠⚠⚠ EJECUTANDO updateMassiveTypeBill ⚠⚠⚠")
    logger.debug(f"ARCHIVO: {__file__}")

    updated = 0
    errors = []

    try:
        total = bills_queryset.count()
    except Exception:
        total = len(bills_queryset)

    logger.debug(f"TOTAL FACTURAS RECIBIDAS PARA PROCESAR: {total}")

    for bill in bills_queryset:
        logger.debug("--------------------------------------------------------")
        logger.debug(
            f"➡ Procesando factura ID {bill.id} | billId {bill.billId} | typeBill actual {bill.typeBill_id}"
        )

        # OJO: ya NO excluimos endosadas/rechazadas aquí,
        # porque justamente hay casos donde están mal en BD y hay que corregirlos.

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
                logger.info("ℹ Factura sin CUFE, asignando UUID_FV")

                if str(bill.typeBill_id) != UUID_FV:
                    try:
                        TypeBill.objects.get(id=UUID_FV)
                        bill.typeBill_id = UUID_FV
                        bill.save(update_fields=["typeBill"])
                        updated += 1
                    except TypeBill.DoesNotExist:
                        logger.error("❗ UUID_FV no existe en TypeBill")
                continue

            # ----------------------------------------------------
            # CONSULTAR EVENTOS (BILLY/DIAN)
            # ----------------------------------------------------
            logger.debug(f"Consultando eventos para CUFE={bill.cufe}")
            result = billEvents_function(bill.cufe, update=True)

            api_events = result.get("events", []) or []
            current_owner = (result.get("currentOwner") or "").strip()

            fields_to_update = []

            # ----------------------------------------------------
            # ACTUALIZAR currentOwner (persistir directo en DB)
            # ----------------------------------------------------
            if current_owner:
                prev_owner = (getattr(bill, "currentOwner", None) or "").strip()
                if current_owner != prev_owner:
                    logger.info(f"📝 currentOwner: '{prev_owner}' → '{current_owner}'")
                    Bill.objects.filter(id=bill.id).update(currentOwner=current_owner)
                    bill.currentOwner = current_owner

            # ----------------------------------------------------
            # SINCRONIZAR EVENTOS
            # ----------------------------------------------------
            if api_events:
                synced = sync_bill_events_v2(bill, api_events)
                logger.info(f"📅 Eventos sincronizados/creados: {synced}")

            # ----------------------------------------------------
            # RECALCULAR typeBill POR CÓDIGOS (NO confiar en result['type'])
            # ----------------------------------------------------
            new_type = compute_type_bill_from_events(api_events)

            if new_type and str(new_type) != str(bill.typeBill_id):
                if is_valid_uuid(new_type):
                    try:
                        TypeBill.objects.get(id=new_type)
                        logger.info(f"🔄 typeBill: {bill.typeBill_id} → {new_type} (billId={bill.billId})")
                        bill.typeBill_id = new_type
                        fields_to_update.append("typeBill")
                        updated += 1
                    except TypeBill.DoesNotExist:
                        logger.error(f"❗ typeBill {new_type} no existe en TypeBill")
                else:
                    logger.error(f"❗ typeBill inválido: {new_type}")

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
# SINCRONIZACIÓN DE EVENTOS V2 (code + DIAN description)
# ============================================================
def sync_bill_events_v2(bill, api_events):
    """
    Evento lógico: (code + dianDescription normalizada)

    Estrategia:
    1) Resolver TypeEvent por (code + dianDescription_norm). Si no existe -> crear.
    2) Evitar duplicar BillEvent:
       - por (bill_id, type_event_id, date) si date existe.
       - si date viene vacío, evita duplicar por (bill_id, type_event_id).
    """
    created = 0

    existing_qs = BillEvent.objects.filter(bill=bill).select_related("event")
    existing_triplets = set()  # (event_id, date)
    existing_pairs = set()     # (event_id)

    for be in existing_qs:
        eid = str(be.event_id)
        existing_pairs.add(eid)
        existing_triplets.add((eid, str(be.date)))

    for ev in api_events:
        code = (ev.get("code") or "").strip()

        # ✅ SOLO DIAN. Si viene vacío, se ignora (y por diseño en front se verá vacío
        # solo si el front construye desde el payload; en DB no creamos TypeEvent “inventado”)
        desc = (ev.get("dianDescription") or "").strip()

        # Si tu proveedor pone la DIAN en otra clave, usa esto:
        # desc = (ev.get("dianDescription") or ev.get("description") or "").strip()

        date = ev.get("date")  # string 'YYYY-MM-DD...' o date (según te llegue)

        if not code or not desc:
            continue

        desc_norm = normalize_description(desc)

        # 1) Resolver/crear TypeEvent por code + dianDescription (normalizada)
        type_event = None
        candidates = TypeEvent.objects.filter(code=code)
        for t in candidates:
            # OJO: aquí se compara contra dianDescription en BD
            if normalize_description(getattr(t, "dianDescription", "") or "") == desc_norm:
                type_event = t
                break

        if not type_event:
            type_event = TypeEvent.objects.create(
                id=uuid.uuid4(),
                code=code,
                supplierDescription="",      # intencionalmente vacío
                dianDescription=desc,        # SOLO DIAN
                created_at=timezone.now(),
                updated_at=timezone.now(),
            )
            logger.info(f"🆕 TypeEvent creado: code={code} dian='{desc[:60]}...' id={type_event.id}")

        eid = str(type_event.id)

        # 2) Evitar duplicados
        if date:
            key = (eid, str(date))
            if key in existing_triplets:
                continue
        else:
            if eid in existing_pairs:
                continue

        # 3) Crear BillEvent
        BillEvent.objects.create(
            id=uuid.uuid4(),
            bill=bill,
            event=type_event,
            date=date,
            created_at=timezone.now(),
            updated_at=timezone.now(),
        )

        if date:
            existing_triplets.add((eid, str(date)))
        existing_pairs.add(eid)

        created += 1

    return created