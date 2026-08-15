from django.db import migrations


def ensure_client_profile_fields(apps, schema_editor):
    Client = apps.get_model("client", "Client")
    table_name = Client._meta.db_table

    with schema_editor.connection.cursor() as cursor:
        existing_columns = {
            column.name
            for column in schema_editor.connection.introspection.get_table_description(cursor, table_name)
        }

    for field_name in ("profile_image", "riesgo"):
        if field_name not in existing_columns:
            schema_editor.add_field(Client, Client._meta.get_field(field_name))


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("client", "0097_ensure_clientaccess_table"),
    ]

    operations = [
        migrations.RunPython(
            ensure_client_profile_fields,
            migrations.RunPython.noop,
            atomic=False,
        ),
    ]
