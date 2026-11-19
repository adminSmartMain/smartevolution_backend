import uuid

from django.db import migrations


MONEY_FIELDS = (
    ("amount", "settledAmount"),
    ("payedAmount", "settledPayedAmount"),
    ("presentValueInvestor", "settledPresentValueInvestor"),
    ("presentValueSF", "settledPresentValueSF"),
    ("investorProfit", "settledInvestorProfit"),
    ("commissionSF", "settledCommissionSF"),
    ("GM", "settledGM"),
)


def move_settlement_audit(apps, schema_editor):
    PreOperation = apps.get_model("operation", "PreOperation")
    OperationLog = apps.get_model("operation", "OperationLog")
    grouped_audit = {}

    for operation in PreOperation.objects.exclude(settlementAudit__isnull=True).iterator():
        updates = {
            original: getattr(operation, settled)
            for original, settled in MONEY_FIELDS
            if getattr(operation, settled) is not None
        }
        if updates:
            PreOperation.objects.filter(pk=operation.pk).update(**updates)

        grouped_audit.setdefault(operation.opId, []).append({
            "operation_id": str(operation.pk),
            "bill_id": str(operation.bill_id),
            "investor_id": str(operation.investor_id),
            "fields": operation.settlementAudit,
        })

    for op_id, rows in grouped_audit.items():
        if not OperationLog.objects.filter(opId=op_id, action="PENNY_ALLOCATION").exists():
            OperationLog.objects.create(
                id=uuid.uuid4(),
                opId=op_id,
                source="SETTLEMENT",
                action="PENNY_ALLOCATION",
                status="INFO",
                message="Penny allocation migrated from operation settlement audit",
                extra_data={
                    "policy": "LARGEST_NOMINAL_HALF_UP_V1",
                    "rows": rows,
                },
            )

    PreOperation.objects.exclude(settlementAudit__isnull=True).update(settlementAudit=None)


class Migration(migrations.Migration):
    dependencies = [("operation", "0034_preoperation_settlement_audit")]

    operations = [migrations.RunPython(move_settlement_audit, migrations.RunPython.noop)]
