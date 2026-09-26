from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
import uuid


RULES = [
    {
        "event_type": "BILL_EXPIRED",
        "label": "Factura vencida",
        "description": "Aviso cuando una factura alcanza su fecha de vencimiento.",
        "permission_code": None,
        "include_entity_creator": True,
    },
    {
        "event_type": "PREOPERATION_PENDING_APPROVAL",
        "label": "Operación pendiente de aprobación",
        "description": "Aviso cuando una preoperación requiere aprobación.",
        "permission_code": "preoperations.approve",
        "include_entity_creator": False,
    },
    {
        "event_type": "ELECTRONIC_SIGNATURE_PENDING",
        "label": "Firma electrónica pendiente",
        "description": "Aviso cuando una operación requiere gestionar su firma electrónica.",
        "permission_code": "operations.create",
        "include_entity_creator": False,
    },
    {
        "event_type": "OPERATION_EXPIRING",
        "label": "Operación próxima a vencer",
        "description": "Aviso cuando una operación activa se aproxima a su vencimiento.",
        "permission_code": "operations.view",
        "include_entity_creator": False,
    },
]


def seed_rules(apps, schema_editor):
    NotificationRule = apps.get_model("notifications", "NotificationRule")
    Permission = apps.get_model("authentication", "Permission")

    for definition in RULES:
        permission = None
        if definition["permission_code"]:
            permission = Permission.objects.filter(
                code=definition["permission_code"],
                state=True,
            ).first()

        NotificationRule.objects.update_or_create(
            event_type=definition["event_type"],
            defaults={
                "label": definition["label"],
                "description": definition["description"],
                "enabled": True,
                "permission": permission,
                "include_entity_creator": definition["include_entity_creator"],
            },
        )


def remove_rules(apps, schema_editor):
    NotificationRule = apps.get_model("notifications", "NotificationRule")
    NotificationRule.objects.filter(
        event_type__in=[item["event_type"] for item in RULES]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0014_user_administration_profile"),
        ("notifications", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="NotificationRule",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("event_type", models.CharField(max_length=100, unique=True)),
                ("label", models.CharField(max_length=160)),
                ("description", models.TextField(blank=True)),
                ("enabled", models.BooleanField(default=True)),
                ("include_entity_creator", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "permission",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="notification_rules",
                        to="authentication.permission",
                    ),
                ),
                (
                    "roles",
                    models.ManyToManyField(
                        blank=True,
                        related_name="notification_rules",
                        to="authentication.role",
                    ),
                ),
                (
                    "include_users",
                    models.ManyToManyField(
                        blank=True,
                        related_name="notification_rule_inclusions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "exclude_users",
                    models.ManyToManyField(
                        blank=True,
                        related_name="notification_rule_exclusions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["event_type"],
            },
        ),
        migrations.RunPython(seed_rules, remove_rules),
    ]
