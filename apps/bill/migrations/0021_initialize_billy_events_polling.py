import hashlib
from datetime import timedelta

from django.db import migrations
from django.utils import timezone


UUID_ENDOSADA = "29113618-6ab8-4633-aa8e-b3d6f242e8a4"
UUID_PAGADA = "e079bea4-401e-41f2-8ccc-e4ac42217728"
UUID_RECHAZADA = "dcec6f03-5dc1-42ea-a525-afada28686da"


def _deterministic_jitter(bill_id, max_seconds):
    """
    Genera un jitter estable a partir del UUID/id de la factura.

    No usamos random para que la migración sea reproducible.
    """

    digest = hashlib.sha256(
        str(bill_id).encode("utf-8")
    ).hexdigest()

    number = int(digest[:8], 16)

    return number % max_seconds


def initialize_billy_polling(apps, schema_editor):
    Bill = apps.get_model("bill", "Bill")

    now = timezone.now()

    bills = (
        Bill.objects
        .filter(
            billyEventsNextCheckAt__isnull=True,
            cufe__isnull=False,
        )
        .exclude(cufe="")
        .exclude(status=4)
        .exclude(
            typeBill_id__in=[
                UUID_PAGADA,
                UUID_RECHAZADA,
            ]
        )
        .only(
            "id",
            "typeBill_id",
            "billyEventsNextCheckAt",
        )
    )

    to_update = []

    for bill in bills.iterator(chunk_size=500):
        type_bill_id = str(bill.typeBill_id)

        if type_bill_id == UUID_ENDOSADA:
            max_seconds = 24 * 60 * 60
        else:
            max_seconds = 60 * 60

        jitter_seconds = _deterministic_jitter(
            bill.id,
            max_seconds,
        )

        bill.billyEventsNextCheckAt = (
            now + timedelta(seconds=jitter_seconds)
        )

        to_update.append(bill)

        if len(to_update) >= 500:
            Bill.objects.bulk_update(
                to_update,
                ["billyEventsNextCheckAt"],
                batch_size=500,
            )
            to_update.clear()

    if to_update:
        Bill.objects.bulk_update(
            to_update,
            ["billyEventsNextCheckAt"],
            batch_size=500,
        )


class Migration(migrations.Migration):

    dependencies = [
        (
            "bill",
            "0020_bill_billyeventsconsecutiveerrors_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(
            initialize_billy_polling,
            migrations.RunPython.noop,
        ),
    ]