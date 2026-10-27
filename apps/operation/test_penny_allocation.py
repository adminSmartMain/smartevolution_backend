from decimal import Decimal

from django.test import SimpleTestCase

from apps.operation.utils.penny_allocation import allocate_pennies, round_cop


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
