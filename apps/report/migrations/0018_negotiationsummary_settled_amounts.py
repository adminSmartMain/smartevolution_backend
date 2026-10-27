from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('report', '0017_remove_sellorderoperation_status_sellorder_opid_and_more')]

    operations = [
        migrations.AddField(model_name='negotiationsummary', name='manualAdjustment', field=models.DecimalField(decimal_places=0, default=0, max_digits=18)),
    ] + [
        migrations.AddField(model_name='negotiationsummary', name=name, field=models.DecimalField(blank=True, decimal_places=0, max_digits=18, null=True))
        for name in (
            'settledFutureValue', 'settledValueToDiscount', 'settledSMDiscount',
            'settledInvestorValue', 'settledInvestorDiscount',
            'settledCommissionValueBeforeTaxes', 'settledOperationValue',
            'settledTableCommission', 'settledIva', 'settledRetIva',
            'settledRetIca', 'settledRetFte', 'settledBillValue',
            'settledTotalDiscounts', 'settledTotal', 'settledPendingToDeposit',
        )
    ]
