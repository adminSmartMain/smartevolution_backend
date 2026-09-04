from django.db import migrations


MIN_REASONABLE_CUFE_LENGTH = 80


def disable_invalid_billy_polling(apps, schema_editor):
    Bill = apps.get_model(
        "bill",
        "Bill",
    )

    bills = Bill.objects.filter(
        billyEventsNextCheckAt__isnull=False,
        cufe__isnull=False,
    ).exclude(
        cufe="",
    )

    ids_to_disable = []

    for bill in bills.iterator(chunk_size=500):
        cufe = (bill.cufe or "").strip()

        if len(cufe) < MIN_REASONABLE_CUFE_LENGTH:
            ids_to_disable.append(
                bill.id
            )

        if len(ids_to_disable) >= 500:
            Bill.objects.filter(
                id__in=ids_to_disable
            ).update(
                billyEventsNextCheckAt=None
            )

            ids_to_disable.clear()

    if ids_to_disable:
        Bill.objects.filter(
            id__in=ids_to_disable
        ).update(
            billyEventsNextCheckAt=None
        )


class Migration(migrations.Migration):

    dependencies = [
        (
            "bill",
            "0021_initialize_billy_events_polling",
        ),
    ]

    operations = [
        migrations.RunPython(
            disable_invalid_billy_polling,
            migrations.RunPython.noop,
        ),
    ]