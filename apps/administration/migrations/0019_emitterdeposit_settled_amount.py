from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('administration', '0018_alter_refund_accountnumber_alter_refund_accounttype_and_more')]

    operations = [
        migrations.AddField(
            model_name='emitterdeposit',
            name='settledAmount',
            field=models.DecimalField(blank=True, decimal_places=0, max_digits=18, null=True),
        ),
    ]
