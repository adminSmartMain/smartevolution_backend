from datetime import date
from types import SimpleNamespace

from apps.operation.api.views.preOperation.index import UploadExcelValidator


class FixedCalculator:
    def calculate(self, row, apply_gm=False):
        return {
            'valorNominal': 900,
            'presentValueInvestor': 800,
            'GM': 0,
        }


def valid_row(**changes):
    row = {
        'row_number': 2,
        'op_id': 'QA-OP-1',
        'op_date': date(2026, 1, 1),
        'emitter_name': 'Emisor QA', 'emitter_id': 'emitter-1',
        'emitter_broker_name': 'Broker QA', 'emitter_broker_id': 'broker-1',
        'payer_name': 'Pagador QA', 'payer_id': 'payer-1',
        'bill_number': 'FAC-1', 'bill_id': 'bill-1', 'bill_balance': 1000,
        'bill_fraction': 1,
        'investor_name': 'Inversionista QA', 'investor_id': 'investor-1',
        'investor_account': '1000000001',
        'fecha_probable': date(2026, 1, 5), 'fecha_fin': date(2026, 1, 10),
        'valor_futuro': 1000, 'porcentaje_descuento': 10,
        'tasa_descuento': 12, 'tasa_inversionista': 10,
    }
    row.update(changes)
    return row


def validator():
    emitter = SimpleNamespace(id='emitter-1')
    payer = SimpleNamespace(id='payer-1')
    investor = SimpleNamespace(id='investor-1')
    bill = SimpleNamespace(id='bill-1')
    account = SimpleNamespace(client_id='investor-1', balance=5000)
    references = {
        'clients_by_id': {'emitter-1': emitter, 'payer-1': payer, 'investor-1': investor},
        'bills_by_id': {'bill-1': bill},
        'brokers_by_id': {'broker-1': SimpleNamespace(id='broker-1')},
        'accounts_by_number': {'1000000001': account},
        'risk_profile_by_client_id': {},
        'investor_broker_by_investor_id': {'investor-1': {'broker_id': 'broker-2', 'broker_name': 'Broker inv'}},
        'next_fraction_by_bill': {'bill-1': 1},
    }
    return UploadExcelValidator(references, FixedCalculator())


def test_accepts_a_complete_valid_excel_row():
    result = validator().validate_rows([valid_row()])

    assert result[0]['has_errors'] is False
    assert result[0]['calculated_payload']['presentValueInvestor'] == 800


def test_marks_missing_required_excel_values_as_errors():
    result = validator().validate_rows([valid_row(investor_account='', valor_futuro=None)])

    messages = {error['field'] for error in result[0]['errors']}
    assert result[0]['has_errors'] is True
    assert {'investor_account', 'valor_futuro'}.issubset(messages)


def test_rejects_duplicate_or_non_consecutive_bill_fractions():
    first = valid_row(row_number=2, bill_fraction=1, valor_futuro=500)
    duplicate = valid_row(row_number=3, bill_fraction=1, valor_futuro=500)

    result = validator().validate_rows([first, duplicate])

    assert all(row['has_errors'] for row in result)
    assert all(any(error['field'] == 'bill_fraction' for error in row['errors']) for row in result)
