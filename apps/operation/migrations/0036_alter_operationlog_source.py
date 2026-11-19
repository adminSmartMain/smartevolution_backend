from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("operation", "0035_move_settlement_audit_to_operation_log")]

    operations = [
        migrations.AlterField(
            model_name="operationlog",
            name="source",
            field=models.CharField(
                choices=[
                    ("SINGLE", "Single Operation"),
                    ("BULK", "Bulk Operation"),
                    ("UPLOAD_EXCEL", "Upload Excel"),
                    ("REGISTER_FROM_UPLOAD", "Register From Upload"),
                    ("PATCH", "Patch Operation"),
                    ("DELETE", "Delete Operation"),
                    ("BILL", "Bill"),
                    ("SETTLEMENT", "Settlement"),
                ],
                max_length=40,
            ),
        ),
    ]
