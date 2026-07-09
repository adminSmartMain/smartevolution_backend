from django.db import migrations


def create_client_access_table_if_missing(apps, schema_editor):
    ClientAccess = apps.get_model("client", "ClientAccess")
    table_name = ClientAccess._meta.db_table

    with schema_editor.connection.cursor() as cursor:
        existing_tables = schema_editor.connection.introspection.table_names(cursor)

    if table_name not in existing_tables:
        schema_editor.create_model(ClientAccess)


class Migration(migrations.Migration):
    dependencies = [
        ("client", "0096_clientaccess"),
    ]

    operations = [
        migrations.RunPython(create_client_access_table_if_missing, migrations.RunPython.noop),
    ]
