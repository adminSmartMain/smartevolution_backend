"""Deterministic COP settlement for operation rows.

This module is deliberately the only place where an operation's monetary rows
are rounded.  Renderers consume the ``settled*`` fields and must never derive
or round a total themselves.
"""
from decimal import Decimal, ROUND_HALF_UP, localcontext


COP_UNIT = Decimal("1")
MONEY_FIELDS = (
    "amount",
    "payedAmount",
    "presentValueInvestor",
    "presentValueSF",
    "investorProfit",
    "commissionSF",
    "GM",
)
SETTLED_FIELD = {
    "amount": "settledAmount",
    "payedAmount": "settledPayedAmount",
    "presentValueInvestor": "settledPresentValueInvestor",
    "presentValueSF": "settledPresentValueSF",
    "investorProfit": "settledInvestorProfit",
    "commissionSF": "settledCommissionSF",
    "GM": "settledGM",
}


def as_decimal(value):
    """Convert inputs without importing binary float noise into calculations."""
    if value in (None, ""):
        return Decimal("0")
    return Decimal(str(value))


def round_cop(value):
    return as_decimal(value).quantize(COP_UNIT, rounding=ROUND_HALF_UP)


def allocate_pennies(raw_amounts, nominal_amounts):
    """Round rows HALF_UP and assign the residual to the largest nominal row."""
    if len(raw_amounts) != len(nominal_amounts):
        raise ValueError("raw_amounts and nominal_amounts must have the same length")
    if not raw_amounts:
        return []

    raw_amounts = [as_decimal(value) for value in raw_amounts]
    rounded = [round_cop(value) for value in raw_amounts]
    consolidated = round_cop(sum(raw_amounts, Decimal("0")))
    delta = consolidated - sum(rounded, Decimal("0"))
    largest_index = max(range(len(nominal_amounts)), key=lambda index: (as_decimal(nominal_amounts[index]), -index))
    rounded[largest_index] += delta
    return rounded


def calculate_operation_values(operation):
    """Return high-precision financial values for a single operation row."""
    nominal = as_decimal(operation.payedAmount)
    investor_rate = as_decimal(operation.investorTax) / Decimal("100")
    discount_rate = as_decimal(operation.discountTax) / Decimal("100")
    days = as_decimal(operation.operationDays)

    with localcontext() as context:
        context.prec = 28
        exponent = days / Decimal("365")
        investor_value = nominal / ((Decimal("1") + investor_rate) ** exponent)
        sf_value = nominal / ((Decimal("1") + discount_rate) ** exponent)

    gm = investor_value * Decimal("0.002") if operation.applyGm else Decimal("0")
    return {
        "amount": as_decimal(operation.amount),
        "payedAmount": nominal,
        "presentValueInvestor": investor_value,
        "presentValueSF": sf_value,
        "investorProfit": nominal - investor_value,
        "commissionSF": investor_value - sf_value,
        "GM": gm,
    }


def settle_operations(operations):
    """Persist a balanced, integer settlement for all rows of an operation.

    ``operations`` must be a deterministic iterable (normally a locked queryset).
    Existing legacy columns are intentionally left untouched so historic records
    are not recalculated.  New documents use only the settled columns.
    """
    operations = list(operations)
    if not operations:
        return operations

    raw_by_operation = [calculate_operation_values(operation) for operation in operations]
    nominals = [values["payedAmount"] for values in raw_by_operation]
    for money_field in MONEY_FIELDS:
        raw_values = [values[money_field] for values in raw_by_operation]
        allocated = allocate_pennies(
            raw_values, nominals
        )
        settled_field = SETTLED_FIELD[money_field]
        for operation, raw_value, value in zip(operations, raw_values, allocated):
            setattr(operation, settled_field, value)
            audit = operation.settlementAudit or {}
            audit[money_field] = {
                'exact_amount': str(raw_value),
                'rounded_amount': str(round_cop(raw_value)),
                'rounding_adjustment': str(value - round_cop(raw_value)),
                'settled_amount': str(value),
            }
            operation.settlementAudit = audit

    for operation in operations:
        operation.save(update_fields=list(SETTLED_FIELD.values()) + ["settlementAudit", "updated_at"])
    return operations


def build_summary_settlement(operations, requested_values):
    """Build persisted header values from already-settled detail rows."""
    totals = {}
    for money_field, settled_field in SETTLED_FIELD.items():
        totals[money_field] = sum(
            (as_decimal(getattr(operation, settled_field)) for operation in operations),
            Decimal("0"),
        )

    investor_discount = totals["payedAmount"] - totals["presentValueInvestor"]
    commission = totals["presentValueInvestor"] - totals["presentValueSF"]
    operation_value = investor_discount + commission
    # Tax configuration is supplied with the summary.  It is still normalized
    # here so every stored COP header is an integer.
    requested = requested_values
    iva = round_cop(requested.get("iva", commission * Decimal("0.19")))
    ret_iva = round_cop(requested.get("retIva", 0))
    ret_ica = round_cop(requested.get("retIca", 0))
    ret_fte = round_cop(requested.get("retFte", 0))
    bill_value = round_cop(commission + iva - ret_iva - ret_ica - ret_fte)

    return {
        "futureValue": totals["amount"],
        "valueToDiscount": totals["payedAmount"],
        "SMDiscount": totals["presentValueSF"],
        "investorValue": totals["presentValueInvestor"],
        "investorDiscount": investor_discount,
        "commissionValueBeforeTaxes": commission,
        "operationValue": operation_value,
        "tableCommission": commission,
        "iva": iva,
        "retIva": ret_iva,
        "retIca": ret_ica,
        "retFte": ret_fte,
        "billValue": bill_value,
        "totalDiscounts": round_cop(requested.get("totalDiscounts", 0)),
        "total": round_cop(requested.get("total", 0)),
        "pendingToDeposit": round_cop(requested.get("pendingToDeposit", 0)),
    }
