from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('operation', '0032_receipt_adjust_void_snapshot')]

    operations = [
        migrations.AddField(model_name='preoperation', name='settledAmount', field=models.DecimalField(blank=True, decimal_places=0, max_digits=18, null=True)),
        migrations.AddField(model_name='preoperation', name='settledPayedAmount', field=models.DecimalField(blank=True, decimal_places=0, max_digits=18, null=True)),
        migrations.AddField(model_name='preoperation', name='settledPresentValueInvestor', field=models.DecimalField(blank=True, decimal_places=0, max_digits=18, null=True)),
        migrations.AddField(model_name='preoperation', name='settledPresentValueSF', field=models.DecimalField(blank=True, decimal_places=0, max_digits=18, null=True)),
        migrations.AddField(model_name='preoperation', name='settledInvestorProfit', field=models.DecimalField(blank=True, decimal_places=0, max_digits=18, null=True)),
        migrations.AddField(model_name='preoperation', name='settledCommissionSF', field=models.DecimalField(blank=True, decimal_places=0, max_digits=18, null=True)),
        migrations.AddField(model_name='preoperation', name='settledGM', field=models.DecimalField(blank=True, decimal_places=0, max_digits=18, null=True)),
    ]
