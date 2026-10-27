from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('operation', '0033_preoperation_settled_amounts')]

    operations = [
        migrations.AddField(
            model_name='preoperation', name='settlementAudit',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
