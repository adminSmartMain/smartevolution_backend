from django.db import migrations


MONEY_FIELDS = (
    ("futureValue", "settledFutureValue"),
    ("valueToDiscount", "settledValueToDiscount"),
    ("SMDiscount", "settledSMDiscount"),
    ("investorValue", "settledInvestorValue"),
    ("investorDiscount", "settledInvestorDiscount"),
    ("commissionValueBeforeTaxes", "settledCommissionValueBeforeTaxes"),
    ("operationValue", "settledOperationValue"),
    ("tableCommission", "settledTableCommission"),
    ("iva", "settledIva"),
    ("retIva", "settledRetIva"),
    ("retIca", "settledRetIca"),
    ("retFte", "settledRetFte"),
    ("billValue", "settledBillValue"),
    ("totalDiscounts", "settledTotalDiscounts"),
    ("total", "settledTotal"),
    ("pendingToDeposit", "settledPendingToDeposit"),
)


def copy_settled_amounts(apps, schema_editor):
    NegotiationSummary = apps.get_model("report", "NegotiationSummary")
    for summary in NegotiationSummary.objects.iterator():
        updates = {
            original: getattr(summary, settled)
            for original, settled in MONEY_FIELDS
            if getattr(summary, settled) is not None
        }
        if updates:
            NegotiationSummary.objects.filter(pk=summary.pk).update(**updates)


class Migration(migrations.Migration):
    dependencies = [("report", "0019_negotiationsummary_settlement_metadata")]

    operations = [migrations.RunPython(copy_settled_amounts, migrations.RunPython.noop)]
