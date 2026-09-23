from datetime import timedelta

from django.apps import apps
from django.db.models import Exists, OuterRef, Q

from apps.bill.utils.updateMassiveTypeBill import (
    UUID_ENDOSADA,
    UUID_PAGADA,
    UUID_RECHAZADA,
)


WATCHLIST_EXIT_TYPE_IDS = {
    UUID_ENDOSADA,
    UUID_PAGADA,
    UUID_RECHAZADA,
}

# Cuando una factura activa no cambia, reducimos gradualmente el polling.
# La regla histórica (1 h) sigue siendo el punto de partida.
UNCHANGED_BACKOFF_HOURS = (3, 6, 12, 24)


def calculate_next_check(
    type_bill_id,
    now,
    on_watchlist=False,
    unchanged_streak=0,
):
    """Calcula el siguiente polling sin alterar las reglas existentes.

    Reglas preservadas:
    - Watchlist activa: 15 minutos.
    - PAGADA / RECHAZADA: no volver a consultar.
    - ENDOSADA: 24 horas.
    - FV, FV-TV y demás estados activos: 1 hora.

    Mejora:
    - Si una factura activa responde correctamente pero repetidamente sin
      cambios, pasa gradualmente a 3 h, 6 h, 12 h y 24 h.
    """
    type_bill_id = str(type_bill_id) if type_bill_id else None

    if on_watchlist:
        return now + timedelta(minutes=15)

    if type_bill_id in {UUID_PAGADA, UUID_RECHAZADA}:
        return None

    if type_bill_id == UUID_ENDOSADA:
        return now + timedelta(hours=24)

    if unchanged_streak > 0:
        index = min(unchanged_streak - 1, len(UNCHANGED_BACKOFF_HOURS) - 1)
        return now + timedelta(hours=UNCHANGED_BACKOFF_HOURS[index])

    return now + timedelta(hours=1)


def filter_eligible_for_billy_polling(queryset):
    """Aplica la regla de elegibilidad automática sin romper Watchlist.

    Reglas de elegibilidad:
    - Sin registros en ``operation``: la factura sigue siendo candidata, pero
      se consulta cada 24 horas para mantener ese universo bajo control.
    - Con operaciones: basta con que exista al menos una fila con ``status != 4``
      para mantenerla en polling. Esto cubre fracciones, múltiples ``opId`` y
      recompras.
    - Solo se excluye cuando existen operaciones y todas están en ``status=4``.

    Watchlist sigue siendo un override explícito/manual y conserva su cadencia.
    """
    PreOperation = apps.get_model("operation", "PreOperation")
    operations = PreOperation.objects.filter(bill_id=OuterRef("pk"))
    live_operations = operations.exclude(status=4)

    return (
        queryset.annotate(
            hasBillyOperation=Exists(operations),
            hasBillyLiveOperation=Exists(live_operations),
        )
        .filter(
            Q(onWatchlist=True)
            | Q(hasBillyLiveOperation=True)
            | Q(hasBillyOperation=False)
        )
    )


def is_bill_eligible_for_billy_polling(bill):
    if bill.onWatchlist:
        return True

    PreOperation = apps.get_model("operation", "PreOperation")
    operations = PreOperation.objects.filter(bill_id=bill.id)

    # Sin operación asociada: se mantiene en polling. La cadencia especial
    # de 24 horas se aplica en ``calculate_bill_next_check``. Solo excluimos
    # el caso donde hay operaciones y todas están canceladas (status=4).
    if not operations.exists():
        return True

    return operations.exclude(status=4).exists()


def calculate_bill_next_check(bill, now, unchanged_streak=0):
    """Cadencia + elegibilidad centralizadas para evitar reglas divergentes.

    La Watchlist sigue teniendo prioridad (15 min). Fuera de Watchlist, una
    factura sin registros asociados en ``operation`` se revisa cada 24 horas,
    independientemente de si es FV, FV-TV u otro tipo activo. Las facturas con
    al menos una operación viva conservan todas las reglas históricas por tipo.
    """
    if not is_bill_eligible_for_billy_polling(bill):
        return None

    # Watchlist es el override explícito/manual y mantiene 15 minutos.
    if bill.onWatchlist:
        return calculate_next_check(
            bill.typeBill_id,
            now,
            on_watchlist=True,
            unchanged_streak=unchanged_streak,
        )

    # Facturas sin operación: polling de baja frecuencia (24 h).
    PreOperation = apps.get_model("operation", "PreOperation")
    has_operation = PreOperation.objects.filter(bill_id=bill.id).exists()
    if not has_operation:
        return now + timedelta(hours=24)

    # Con al menos una operación viva, se conservan las reglas existentes:
    # ENDOSADA 24 h; FV/FV-TV y demás activas 1 h base; estados finales no
    # vuelven a consultarse; el backoff por ausencia de cambios sigue vigente.
    return calculate_next_check(
        bill.typeBill_id,
        now,
        on_watchlist=False,
        unchanged_streak=unchanged_streak,
    )


def apply_watchlist_exit_rule(bill):
    """Desactiva Watchlist al entrar a estados que ya no requieren intensidad."""
    if not bill.onWatchlist:
        return False

    type_bill_id = str(bill.typeBill_id) if bill.typeBill_id else None

    if type_bill_id not in WATCHLIST_EXIT_TYPE_IDS:
        return False

    bill.onWatchlist = False
    bill.watchlistActivatedAt = None
    bill.watchlistActivatedBy = None
    bill.save(
        update_fields=[
            "onWatchlist",
            "watchlistActivatedAt",
            "watchlistActivatedBy",
        ]
    )

    return True
