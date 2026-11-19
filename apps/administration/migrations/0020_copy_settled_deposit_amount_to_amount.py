from django.db import migrations


def copy_settled_amounts(apps, schema_editor):
    EmitterDeposit = apps.get_model("administration", "EmitterDeposit")
    for deposit in EmitterDeposit.objects.exclude(settledAmount__isnull=True).iterator():
        EmitterDeposit.objects.filter(pk=deposit.pk).update(amount=deposit.settledAmount)


class Migration(migrations.Migration):
    dependencies = [("administration", "0019_emitterdeposit_settled_amount")]

    operations = [migrations.RunPython(copy_settled_amounts, migrations.RunPython.noop)]
