from django.db import migrations


def ensure_client_role_tables(apps, schema_editor):
    ClientRole = apps.get_model("client", "ClientRole")
    ClientRoleAssignment = apps.get_model("client", "ClientRoleAssignment")
    connection = schema_editor.connection

    with connection.cursor() as cursor:
        existing_tables = set(connection.introspection.table_names(cursor))

    if ClientRole._meta.db_table not in existing_tables:
        schema_editor.create_model(ClientRole)
        existing_tables.add(ClientRole._meta.db_table)

    if ClientRoleAssignment._meta.db_table not in existing_tables:
        schema_editor.create_model(ClientRoleAssignment)


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("client", "0099_ensure_risk_level_schema"),
    ]

    operations = [
        migrations.RunPython(
            ensure_client_role_tables,
            migrations.RunPython.noop,
            atomic=False,
        ),
    ]
