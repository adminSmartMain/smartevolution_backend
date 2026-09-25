from django.db import migrations, models


def seed_bill_expiring_rule(apps, schema_editor):
    NotificationRule = apps.get_model("notifications", "NotificationRule")
    NotificationRule.objects.update_or_create(
        event_type="BILL_EXPIRING",
        defaults={
            "label": "Factura próxima a vencer",
            "description": "Aviso cuando una factura elegible se encuentra a siete días o menos de su vencimiento.",
            "enabled": True,
            "send_email": False,
            "include_entity_creator": True,
        },
    )


def remove_bill_expiring_rule(apps, schema_editor):
    NotificationRule = apps.get_model("notifications", "NotificationRule")
    NotificationRule.objects.filter(event_type="BILL_EXPIRING").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0002_notification_rules"),
    ]

    operations = [
        migrations.AddField(
            model_name="notificationrule",
            name="send_email",
            field=models.BooleanField(
                default=False,
                help_text="También envía la notificación al correo del destinatario.",
            ),
        ),
        migrations.RunPython(seed_bill_expiring_rule, remove_bill_expiring_rule),
    ]
