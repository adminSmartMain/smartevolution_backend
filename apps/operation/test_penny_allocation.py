from decimal import Decimal

from django.test import SimpleTestCase

from apps.operation.utils.penny_allocation import allocate_pennies, round_cop, settle_operations


class OperationStub:
    def __init__(self, identifier, nominal):
        self.id = identifier
        self.bill_id = f"bill-{identifier}"
        self.investor_id = f"investor-{identifier}"
        self.amount = nominal
        self.payedAmount = nominal
        self.investorTax = 10
        self.discountTax = 20
        self.operationDays = 30
        self.applyGm = False
        self.presentValueInvestor = 0
        self.presentValueSF = 0
        self.investorProfit = 0
        self.commissionSF = 0
        self.GM = 0
        self.saved_fields = None

    def save(self, update_fields):
        self.saved_fields = update_fields


class PennyAllocationTests(SimpleTestCase):
    def test_assigns_positive_residual_to_largest_nominal_row(self):
        values = [Decimal('10.49'), Decimal('10.49'), Decimal('10.49')]

        result = allocate_pennies(values, [100, 300, 200])

        self.assertEqual(result, [Decimal('10'), Decimal('11'), Decimal('10')])
        self.assertEqual(sum(result), round_cop(sum(values)))

    def test_assigns_negative_residual_to_largest_nominal_row(self):
        values = [Decimal('10.51'), Decimal('10.51'), Decimal('10.51')]

        result = allocate_pennies(values, [100, 300, 200])

        self.assertEqual(result, [Decimal('11'), Decimal('10'), Decimal('11')])
        self.assertEqual(sum(result), round_cop(sum(values)))

    def test_tie_breaker_is_stable_by_detail_order(self):
        values = [Decimal('1.49'), Decimal('1.49')]

        result = allocate_pennies(values, [100, 100])

        self.assertEqual(result, [Decimal('2'), Decimal('1')])
        self.assertEqual(sum(result), round_cop(sum(values)))

    def test_settlement_replaces_source_amounts_and_returns_a_single_audit_payload(self):
        operations = [OperationStub("a", 100), OperationStub("b", 300)]

        settled, audit = settle_operations(operations)

        self.assertEqual(settled, operations)
        self.assertEqual(audit["policy"], "LARGEST_NOMINAL_HALF_UP_V1")
        self.assertEqual(len(audit["rows"]), 2)
        self.assertIn("exact_amount", audit["rows"][0]["fields"]["presentValueInvestor"])
        self.assertIn("amount", operations[0].saved_fields)
        self.assertNotIn("settledAmount", operations[0].saved_fields)
