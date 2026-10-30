from decimal import Decimal
from types import SimpleNamespace

import pytest

from apps.operation.utils.penny_allocation import (
    allocate_pennies,
    as_decimal,
    build_summary_settlement,
    round_cop,
)


def test_normalizes_blank_amounts_without_float_noise():
    assert as_decimal(None) == Decimal("0")
    assert as_decimal("") == Decimal("0")
    assert as_decimal(0.1) == Decimal("0.1")


def test_rounds_cop_half_up_for_positive_and_negative_amounts():
    assert round_cop("10.5") == Decimal("11")
    assert round_cop("-10.5") == Decimal("-11")


def test_rejects_mismatched_operation_and_nominal_rows():
    with pytest.raises(ValueError, match="same length"):
        allocate_pennies([Decimal("10")], [Decimal("10"), Decimal("20")])


def test_returns_no_rows_when_there_are_no_amounts_to_settle():
    assert allocate_pennies([], []) == []


def test_builds_summary_only_from_already_settled_values():
    operation = SimpleNamespace(
        settledAmount=Decimal("100"),
        settledPayedAmount=Decimal("90"),
        settledPresentValueInvestor=Decimal("80"),
        settledPresentValueSF=Decimal("70"),
        settledInvestorProfit=Decimal("10"),
        settledCommissionSF=Decimal("10"),
        settledGM=Decimal("0"),
    )

    summary = build_summary_settlement(
        [operation],
        {"iva": "1.5", "retIva": "1", "retIca": "0", "retFte": "0"},
    )

    assert summary["futureValue"] == Decimal("100")
    assert summary["investorDiscount"] == Decimal("10")
    assert summary["commissionValueBeforeTaxes"] == Decimal("10")
    assert summary["iva"] == Decimal("2")
    assert summary["billValue"] == Decimal("11")
