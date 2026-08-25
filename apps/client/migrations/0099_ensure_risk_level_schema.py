import uuid

from django.db import migrations


def ensure_risk_level_schema(apps, schema_editor):
    LevelRisk = apps.get_model("client", "LevelRisk")
    RiskProfile = apps.get_model("client", "RiskProfile")
    connection = schema_editor.connection

    with connection.cursor() as cursor:
        tables = set(connection.introspection.table_names(cursor))

    if LevelRisk._meta.db_table not in tables:
        schema_editor.create_model(LevelRisk)

    with connection.cursor() as cursor:
        risk_profile_columns = {
            column.name
            for column in connection.introspection.get_table_description(
                cursor, RiskProfile._meta.db_table
            )
        }

    risk_levels_field = RiskProfile._meta.get_field("riskLevels")
    if risk_levels_field.column not in risk_profile_columns:
        schema_editor.add_field(RiskProfile, risk_levels_field)

    default_level, _ = LevelRisk.objects.get_or_create(
        level="No aplica",
        min_score=0,
        max_score=0,
        defaults={
            "id": str(uuid.uuid4()),
            "interpretation": (
                "Nivel predeterminado mientras se completa la evaluación de riesgo."
            ),
        },
    )
    RiskProfile.objects.filter(riskLevels__isnull=True).update(riskLevels=default_level)


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("client", "0098_ensure_client_profile_fields"),
    ]

    operations = [
        migrations.RunPython(ensure_risk_level_schema, migrations.RunPython.noop),
    ]
