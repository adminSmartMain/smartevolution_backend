from datetime import timedelta

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


def calculate_next_check(
    type_bill_id,
    now,
    on_watchlist=False,
):
    """
    Calcula cuándo debe volver a consultarse una factura en Billy.

    Reglas:
    - Watchlist activa: volver a consultar en 15 minutos.
    - PAGADA: no volver a consultar.
    - RECHAZADA: no volver a consultar.
    - ENDOSADA: volver a consultar en 24 horas.
    - Cualquier otro estado: volver a consultar en 1 hora.
    """

    type_bill_id = str(type_bill_id) if type_bill_id else None

    if on_watchlist:
        return now + timedelta(minutes=15)

    if type_bill_id in {
        UUID_PAGADA,
        UUID_RECHAZADA,
    }:
        return None

    if type_bill_id == UUID_ENDOSADA:
        return now + timedelta(hours=24)

    return now + timedelta(hours=1)


def apply_watchlist_exit_rule(bill):
    """
    Desactiva Watchlist cuando la factura alcanza un estado que ya no
    requiere seguimiento intensivo. Devuelve True si cambió el estado.
    """
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
