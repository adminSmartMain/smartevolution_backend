from datetime import timedelta

from apps.bill.utils.updateMassiveTypeBill import (
    UUID_ENDOSADA,
    UUID_PAGADA,
    UUID_RECHAZADA,
)


def calculate_next_check(type_bill_id, now):
    """
    Calcula cuándo debe volver a consultarse una factura en Billy.

    Reglas:
    - PAGADA: no volver a consultar.
    - RECHAZADA: no volver a consultar.
    - ENDOSADA: volver a consultar en 24 horas.
    - Cualquier otro estado: volver a consultar en 1 hora.
    """

    type_bill_id = str(type_bill_id) if type_bill_id else None

    if type_bill_id in {
        UUID_PAGADA,
        UUID_RECHAZADA,
    }:
        return None

    if type_bill_id == UUID_ENDOSADA:
        return now + timedelta(hours=24)

    return now + timedelta(hours=1)