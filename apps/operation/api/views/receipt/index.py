# REST Framework imports
from rest_framework.decorators import APIView
# Models
from apps.operation.models import Receipt
# Serializers
from apps.operation.api.serializers.index import ReceiptSerializer, ReceiptReadOnlySerializer
# Utils
from apps.base.utils.index import response, BaseAV
# Decorators
from apps.base.decorators.index import checkRole
from django.db.models import Q, Count
import logging

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from math import pow

from django.db import transaction
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import json
from openpyxl import load_workbook
from apps.operation.models import PreOperation, Receipt
from apps.operation.api.serializers.index import ReceiptSerializer

# Configurar el logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Crear un handler de consola y definir el nivel
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Crear un formato para los mensajes de log
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Añadir el handler al logger
logger.addHandler(console_handler)






















RECEIPT_TYPE_LABELS = {
    "3d461dea-0545-4a92-a847-31b8327bf033": "Cancelado Anticipado",
    "62b0ca1e-f999-4a76-a07f-be1fe4f38cfb": "Cancelado Vencido",
    "d40e91b1-fb6c-4c61-9da8-78d4f258181d": "Parcial vigente",
    "db1d1fa4-e467-4fde-9aee-bbf4008d688b": "Cancelado Vigente",
    "ed85d2bc-1a4b-45ae-b2fd-f931527d9f7f": "Parcial vencido",
    "edd99cf7-6f47-4c82-a4fd-f13b4c60a0c0": "Parcial anticipado",
}


def get_receipt_label_from_type_id(type_id):
    return RECEIPT_TYPE_LABELS.get(str(type_id), "")

RECEIPT_TYPE_IDS = {
    "CANCELED_ANTICIPATED": "3d461dea-0545-4a92-a847-31b8327bf033",
    "PARTIAL_ANTICIPATED": "edd99cf7-6f47-4c82-a4fd-f13b4c60a0c0",
    "CANCELED_EXPIRED": "62b0ca1e-f999-4a76-a07f-be1fe4f38cfb",
    "PARTIAL_EXPIRED": "ed85d2bc-1a4b-45ae-b2fd-f931527d9f7f",
    "CANCELED_CURRENT": "db1d1fa4-e467-4fde-9aee-bbf4008d688b",
    "PARTIAL_CURRENT": "d40e91b1-fb6c-4c61-9da8-78d4f258181d",
}

STATUS_KEYS = {
    "CANCELED_ANTICIPATED": "canceled_anticipated",
    "PARTIAL_ANTICIPATED": "partial_anticipated",
    "CANCELED_EXPIRED": "canceled_expired",
    "PARTIAL_EXPIRED": "partial_expired",
    "CANCELED_CURRENT": "canceled_current",
    "PARTIAL_CURRENT": "partial_current",
}

SUMMARY_KEYS = {
    "CANCELED_ANTICIPATED": "canceledAnticipated",
    "PARTIAL_ANTICIPATED": "partialAnticipated",
    "CANCELED_EXPIRED": "canceledExpired",
    "PARTIAL_EXPIRED": "partialExpired",
    "CANCELED_CURRENT": "canceledCurrent",
    "PARTIAL_CURRENT": "partialCurrent",
}


def to_decimal(value):
    if value is None or value == "":
        return Decimal("0")
    return Decimal(str(value))


def money(value):
    return to_decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def parse_date(value):
    if not value:
        return None

    if hasattr(value, "date"):
        return value.date()

    if isinstance(value, str):
        clean = value[:10]
        return datetime.strptime(clean, "%Y-%m-%d").date()

    return value


def format_date(value):
    if not value:
        return None

    if hasattr(value, "isoformat"):
        return value.isoformat()

    return str(value)


def get_client_name(client):
    if not client:
        return ""

    full_name = f"{getattr(client, 'first_name', '') or ''} {getattr(client, 'last_name', '') or ''}".strip()

    return (
        getattr(client, "social_reason", None)
        or getattr(client, "full_name", None)
        or full_name
        or getattr(client, "document_number", None)
        or ""
    )


def get_account_client(account):
    if not account:
        return None

    client = getattr(account, "client", None)

    if client:
        return client

    client_id = getattr(account, "client_id", None)

    if client_id:
        try:
            from apps.client.models import Client
            return Client.objects.filter(id=client_id).first()
        except Exception:
            return None

    return None


def get_account_number(account):
    if not account:
        return ""

    return (
        getattr(account, "account_number", None)
        or getattr(account, "number", None)
        or str(getattr(account, "id", "") or "")
    )


def get_operation_discount_tax(op):
    return (
        getattr(op, "discountTax", None)
        or getattr(op, "discount_tax", None)
        or getattr(op, "tax", None)
        or 0
    )


def get_operation_investor_tax(op):
    return (
        getattr(op, "investorTax", None)
        or getattr(op, "investor_tax", None)
        or 0
    )


def calc_additional_interests(base_amount, tax, days):
    base_amount = float(base_amount or 0)
    tax = float(tax or 0)
    days = int(days or 0)

    if base_amount <= 0 or tax <= 0 or days <= 0:
        return Decimal("0.00")

    grow_factor = pow(1 + (tax / 100), days / 365)
    total = base_amount * grow_factor
    interest = total - base_amount

    return money(interest)


def calc_future_value_recalculation(present_value, investor_tax, calculated_days):
    present_value = float(present_value or 0)
    investor_tax = float(investor_tax or 0)
    calculated_days = int(calculated_days or 0)

    if present_value <= 0 or investor_tax <= 0 or calculated_days <= 0:
        return Decimal("0.00")

    value = present_value * pow(1 + (investor_tax / 100), calculated_days / 365)
    return money(value)


def get_previous_receipt_data(op):
    receipts = Receipt.objects.filter(
        operation_id=op.id,
        state=1,
    ).order_by("-date", "-created_at")

    last_receipt = receipts.first()

    if not last_receipt:
        return {
            "lastDate": None,
            "payedAmount": Decimal("0"),
            "interest": Decimal("0"),
        }

    total_previous_payed = Decimal("0")
    total_previous_interest = Decimal("0")

    for receipt in receipts:
        total_previous_payed += to_decimal(getattr(receipt, "payedAmount", 0))
        total_previous_interest += to_decimal(getattr(receipt, "additionalInterests", 0))

    return {
        "lastDate": getattr(last_receipt, "date", None),
        "payedAmount": total_previous_payed,
        "interest": total_previous_interest,
    }


def get_state(application_date, expiration_date):
    if application_date < expiration_date:
        return "anticipada"

    if application_date > expiration_date:
        return "vencida"

    return "vigente"


def get_receipt_type_key(state_name, canceled):
    if canceled:
        if state_name == "anticipada":
            return "CANCELED_ANTICIPATED"
        if state_name == "vencida":
            return "CANCELED_EXPIRED"
        return "CANCELED_CURRENT"

    if state_name == "anticipada":
        return "PARTIAL_ANTICIPATED"
    if state_name == "vencida":
        return "PARTIAL_EXPIRED"
    return "PARTIAL_CURRENT"

def normalize_to_date(value):
        if not value:
            return None

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        parsed = parse_date(value)

        if isinstance(parsed, datetime):
            return parsed.date()

        return parsed

def build_receipt_preview_row(op, application_date, receipt_status_id=None, payed_amount_override=None):
    bill = op.bill
    account = op.clientAccount

    if not bill:
        return None

    investor_client = get_account_client(account)

    op_date = normalize_to_date(getattr(op, "opDate", None))

    expiration_date = normalize_to_date(
        getattr(op, "opExpiration", None)
        or getattr(bill, "expirationDate", None)
        or getattr(op, "expirationDate", None)
        or op_date
    )

    application_date = normalize_to_date(application_date)

    if not op_date:
        op_date = application_date

    if not expiration_date:
        expiration_date = op_date



    current_balance = money(
        getattr(op, "opPendingAmount", None)
        or getattr(bill, "currentBalance", None)
        or getattr(op, "amount", None)
        or 0
    )

    nominal_value = money(
        getattr(op, "payedAmount", None)
        or getattr(bill, "billValue", None)
        or getattr(bill, "total", None)
        or current_balance
    )

    future_value = money(
        getattr(op, "amount", None)
        or current_balance
    )

    present_value_investor_base = money(
        getattr(op, "presentValueInvestor", None)
        or nominal_value
    )

    discount_tax = to_decimal(get_operation_discount_tax(op))
    investor_tax = to_decimal(get_operation_investor_tax(op))

    previous_receipt = get_previous_receipt_data(op)
    last_date = normalize_to_date(previous_receipt.get("lastDate"))

    previous_payed_amount = money(previous_receipt["payedAmount"])
    previous_interest = money(previous_receipt["interest"])

    payed_amount = money(
    payed_amount_override
    if payed_amount_override is not None
    else 0
)

    receipt_status_text = str(receipt_status_id or "")

    state_name = get_state(application_date, expiration_date)

    real_days = max((application_date - op_date).days, 0)
    calculated_days = real_days

    additional_days = 0
    additional_interests = Decimal("0.00")
    investor_interests = Decimal("0.00")
    additional_interests_sm = Decimal("0.00")
    future_value_recalculation = Decimal("0.00")
    table_remaining = Decimal("0.00")
    remaining = Decimal("0.00")
    present_value_investor = Decimal("0.00")

    # Igual que el individual: primero calculamos intereses y pendiente,
    # luego decidimos si es cancelado o parcial.
    if state_name == "vencida":
        if last_date and previous_interest > 0:
            additional_days = max((application_date - last_date).days, 0)
        else:
            additional_days = max((application_date - expiration_date).days, 0)

        base_for_interest = nominal_value

        if previous_payed_amount > 0:
            base_for_interest = money(
                nominal_value - (previous_payed_amount - previous_interest)
            )

        additional_interests = calc_additional_interests(
            base_for_interest,
            discount_tax,
            additional_days,
        )

        investor_interests = calc_additional_interests(
            base_for_interest,
            investor_tax,
            additional_days,
        )

        additional_interests_sm = money(additional_interests - investor_interests)

    elif state_name == "anticipada":
        additional_days = 0
        additional_interests = Decimal("0.00")
        investor_interests = Decimal("0.00")
        additional_interests_sm = Decimal("0.00")

    else:
        additional_days = 0
        additional_interests = Decimal("0.00")
        investor_interests = Decimal("0.00")
        additional_interests_sm = Decimal("0.00")

    # Pendiente real igual al individual:
    # el pago que amortiza operación es payedAmount - additionalInterests.
    net_for_pending = money(payed_amount - additional_interests)

    if net_for_pending >= current_balance:
        pending_after = Decimal("0.00")
        remaining = money(net_for_pending - current_balance)
        canceled = True
    else:
        pending_after = money(current_balance - net_for_pending)
        remaining = Decimal("0.00")
        canceled = False

    # Si es recaudo de tipo recompra / estado especial, el individual deja remanentes en 0.
    if receipt_status_text == "ea8518e8-168a-46d7-b56a-1286bf0037cd":
        remaining = Decimal("0.00")
        table_remaining = Decimal("0.00")

    # Cálculos dependientes de cancelado/parcial, ya con canceled correcto.
    if state_name == "anticipada":
        if canceled:
            future_value_recalculation = calc_future_value_recalculation(
                present_value_investor_base,
                investor_tax,
                calculated_days,
            )

            if receipt_status_text != "ea8518e8-168a-46d7-b56a-1286bf0037cd":
                table_remaining = money(nominal_value - future_value_recalculation)
            else:
                table_remaining = Decimal("0.00")

            if previous_payed_amount > 0:
                present_value_investor = money(
                    future_value_recalculation - previous_payed_amount
                )
            else:
                present_value_investor = future_value_recalculation
        else:
            future_value_recalculation = Decimal("0.00")
            table_remaining = Decimal("0.00")
            present_value_investor = payed_amount

    elif state_name == "vencida":
        future_value_recalculation = Decimal("0.00")
        table_remaining = Decimal("0.00")

        if canceled:
            if previous_payed_amount > 0:
                present_value_investor = money(
                    payed_amount - additional_interests - remaining
                )
            else:
                present_value_investor = nominal_value
        else:
            present_value_investor = money(payed_amount - additional_interests)

    else:
        future_value_recalculation = Decimal("0.00")
        table_remaining = Decimal("0.00")

        if canceled:
            if previous_payed_amount > 0:
                present_value_investor = money(payed_amount - remaining)
            else:
                present_value_investor = nominal_value
        else:
            present_value_investor = payed_amount

    if present_value_investor < Decimal("0.00"):
        present_value_investor = Decimal("0.00")

    receipt_type_key = get_receipt_type_key(state_name, canceled)
    receipt_type_id = RECEIPT_TYPE_IDS[receipt_type_key]
    status_key = STATUS_KEYS[receipt_type_key]

    to_collect = money(current_balance + additional_interests)

    investor_name = get_client_name(investor_client)
    account_number = get_account_number(account)

    fraction = (
        getattr(op, "fraction", None)
        or getattr(op, "billFraction", None)
        or getattr(bill, "fraction", None)
        or 1
    )

    return {
        "id": str(op.id),
        "preOperationId": str(op.id),
        "operation": str(op.id),

        "billUniqueId": str(bill.id),
        "billId": getattr(bill, "billId", None),
        "fraction": int(fraction or 1),

        "opId": getattr(op, "opId", None),
        "opDate": format_date(op_date),
        "periodStart": format_date(op_date),
        "periodEnd": format_date(expiration_date),

        "emitterId": str(getattr(op, "emitter_id", "") or ""),
        "emitterName": getattr(bill, "emitterName", None) or "",
        "payerId": str(getattr(op, "payer_id", "") or ""),
        "payerName": getattr(bill, "payerName", None) or "",

        "account": str(account.id) if account else None,
        "accountId": str(account.id) if account else None,
        "accountNumber": account_number,
        "investorName": investor_name,

        "futureValue": float(money(future_value)),
        "nominalValue": float(money(nominal_value)),
        "currentBalance": float(money(current_balance)),
        "pending": float(money(pending_after)),
        "payedAmount": float(money(payed_amount)),
        "toCollect": float(money(to_collect)),

        "realDays": real_days,
        "calculatedDays": calculated_days,
        "additionalDays": additional_days,

        "additionalInterests": float(money(additional_interests)),
        "interests": float(money(additional_interests)),
        "investorInterests": float(money(investor_interests)),
        "additionalInterestsSM": float(money(additional_interests_sm)),
        "tableInterests": float(money(additional_interests_sm)),
        "remaining": float(money(remaining)),
        "tableRemaining": float(money(table_remaining)),
        "futureValueRecalculation": float(money(future_value_recalculation)),
        "presentValueInvestor": float(money(present_value_investor)),

        "state": state_name,
        "statusKey": status_key,
        "receiptType": receipt_type_id,
        "typeReceipt": receipt_type_id,
        "receiptStatus": receipt_status_id,

        "previousPayedAmount": float(money(previous_payed_amount)),
        "previousInterest": float(money(previous_interest)),
        "lastDate": format_date(previous_receipt["lastDate"]),
    }

class MassiveReceiptPreview(APIView):
    def post(self, request):
        application_date = request.data.get("applicationDate")
        receipt_status_id = request.data.get("receiptStatus")
        operations = request.data.get("operations", [])

        if not application_date:
            return Response(
                {"error": True, "message": "Se requiere applicationDate"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(operations, list) or len(operations) == 0:
            return Response(
                {"error": True, "message": "Se requieren operaciones"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            application_date = parse_date(application_date)
        except Exception:
            return Response(
                {"error": True, "message": "applicationDate inválida"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        preoperation_ids = [
            item.get("preOperationId") or item.get("id")
            for item in operations
            if item.get("preOperationId") or item.get("id")
        ]

        payed_by_operation = {
            str(item.get("preOperationId") or item.get("id")): item.get("payedAmount")
            for item in operations
            if item.get("preOperationId") or item.get("id")
        }

        preoperations = (
            PreOperation.objects
            .filter(id__in=preoperation_ids, status=1, state=1)
            .select_related("bill", "clientAccount")
        )

        rows = []
        summary = {
            "canceledAnticipated": 0,
            "partialAnticipated": 0,
            "canceledExpired": 0,
            "partialExpired": 0,
            "canceledCurrent": 0,
            "partialCurrent": 0,
        }

        for op in preoperations:
            try:
                row = build_receipt_preview_row(
                    op,
                    application_date,
                    receipt_status_id=receipt_status_id,
                    payed_amount_override=payed_by_operation.get(str(op.id)),
                )
            except ValueError as error:
                return Response(
                    {
                        "error": True,
                        "message": str(error),
                        "operation": str(op.id),
                        "opId": getattr(op, "opId", None),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not row:
                continue

            rows.append(row)

            receipt_key = None
            for key, value in STATUS_KEYS.items():
                if value == row["statusKey"]:
                    receipt_key = key
                    break

            if receipt_key and receipt_key in SUMMARY_KEYS:
                summary[SUMMARY_KEYS[receipt_key]] += 1

        return Response(
            {
                "error": False,
                "summary": summary,
                "count": len(rows),
                "data": rows,
            },
            status=status.HTTP_200_OK,
        )


def build_field_errors(errors):
    field_errors = {}

    for error in errors:
        field = error.get("field")
        message = error.get("message")

        if field and message:
            field_errors[field] = message

    return field_errors


def build_receipt_summary_from_rows(rows):
    summary = {
        "canceledAnticipated": 0,
        "partialAnticipated": 0,
        "canceledExpired": 0,
        "partialExpired": 0,
        "canceledCurrent": 0,
        "partialCurrent": 0,
    }

    for row in rows:
        status_key = row.get("statusKey")
        receipt_key = None

        for key, value in STATUS_KEYS.items():
            if value == status_key:
                receipt_key = key
                break

        if receipt_key and receipt_key in SUMMARY_KEYS:
            summary[SUMMARY_KEYS[receipt_key]] += 1

    return summary

class MassiveReceiptUploadExcelParser:
    HEADER_ROW = 6

    HEADER_ALIASES = {
        "FACTURA": ["FACTURA"],
        "FRACCION": ["FRACCIÓN", "FRACCION"],
        "OPID": ["OPID", "OP ID"],
        "PERIODO_INICIO": ["PERIODO INICIO", "FECHA INICIO"],
        "PERIODO_FIN": ["PERIODO FIN", "FECHA FIN"],
        "POR_COBRAR": ["POR COBRAR"],
        "DIAS_CALCULO": ["DÍAS CÁLCULO", "DIAS CALCULO"],
        "MONTO_APLICACION": ["MONTO APLICACIÓN", "MONTO APLICACION"],
        "PREOPERACION": ["PREOPERACIÓN", "PREOPERACION"],
        "ID_FACTURA": ["ID FACTURA"],
    }

    def normalize_header(self, value):
        if value is None:
            return ""

        return (
            str(value)
            .strip()
            .upper()
            .replace("\n", " ")
            .replace("  ", " ")
        )

    def find_col(self, headers, key):
        aliases = self.HEADER_ALIASES.get(key, [])

        for alias in aliases:
            normalized_alias = self.normalize_header(alias)
            if normalized_alias in headers:
                return headers[normalized_alias]

        return None

    def get_cell_value(self, sheet, row_number, col):
        if not col:
            return None

        return sheet.cell(row_number, col).value

    def parse(self, excel_file):
        workbook = load_workbook(excel_file, data_only=True)
        sheet = workbook.active

        headers = {}

        for col in range(1, sheet.max_column + 1):
            value = self.normalize_header(sheet.cell(self.HEADER_ROW, col).value)
            if value:
                headers[value] = col

        required_keys = [
            "FACTURA",
            "FRACCION",
            "OPID",
            "PERIODO_INICIO",
            "PERIODO_FIN",
            "DIAS_CALCULO",
            "MONTO_APLICACION",
            "PREOPERACION",
            "ID_FACTURA",
        ]

        missing = [
            key
            for key in required_keys
            if not self.find_col(headers, key)
        ]

        if missing:
            raise ValueError(
                "El Excel no tiene las columnas requeridas para recaudos: "
                + ", ".join(missing)
            )

        col_factura = self.find_col(headers, "FACTURA")
        col_fraccion = self.find_col(headers, "FRACCION")
        col_opid = self.find_col(headers, "OPID")
        col_inicio = self.find_col(headers, "PERIODO_INICIO")
        col_fin = self.find_col(headers, "PERIODO_FIN")
        col_por_cobrar = self.find_col(headers, "POR_COBRAR")
        col_dias_calculo = self.find_col(headers, "DIAS_CALCULO")
        col_monto = self.find_col(headers, "MONTO_APLICACION")
        col_preoperacion = self.find_col(headers, "PREOPERACION")
        col_id_factura = self.find_col(headers, "ID_FACTURA")

        rows = []

        for row_number in range(self.HEADER_ROW + 1, sheet.max_row + 1):
            bill_number = self.get_cell_value(sheet, row_number, col_factura)
            preoperation_id = self.get_cell_value(sheet, row_number, col_preoperacion)

            if not bill_number and not preoperation_id:
                continue

            rows.append({
                "rowNumber": row_number,
                "billNumber": str(bill_number).strip() if bill_number else "",
                "billId": str(self.get_cell_value(sheet, row_number, col_id_factura) or "").strip(),
                "fraction": self.get_cell_value(sheet, row_number, col_fraccion),
                "opId": self.get_cell_value(sheet, row_number, col_opid),
                "periodStart": self.get_cell_value(sheet, row_number, col_inicio),
                "periodEnd": self.get_cell_value(sheet, row_number, col_fin),
                "toCollect": self.get_cell_value(sheet, row_number, col_por_cobrar),
                "calculatedDays": self.get_cell_value(sheet, row_number, col_dias_calculo),
                "payedAmount": self.get_cell_value(sheet, row_number, col_monto),
                "preOperationId": str(preoperation_id).strip() if preoperation_id else "",
                "operation": str(preoperation_id).strip() if preoperation_id else "",
            })

        return rows


class MassiveReceiptUploadExcel(APIView):
    def post(self, request):
        excel_file = request.FILES.get("uploadExcel")

        if not excel_file:
            return Response(
                {"message": "No se recibió el archivo uploadExcel"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        raw_context = request.data.get("context")
        upload_context = None

        if raw_context:
            try:
                upload_context = json.loads(raw_context)
            except Exception:
                return Response(
                    {"message": "El contexto de carga es inválido"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if not upload_context:
            return Response(
                {"message": "Se requiere contexto de carga para validar recaudos"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        application_date = upload_context.get("applicationDate")
        receipt_status_id = upload_context.get("receiptStatus")
        expected_rows = upload_context.get("rows") or []

        if not application_date:
            return Response(
                {"message": "El contexto no contiene Fecha Aplicación"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not receipt_status_id:
            return Response(
                {"message": "El contexto no contiene Estado de Recaudo"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            application_date = parse_date(application_date)
        except Exception:
            return Response(
                {"message": "Fecha Aplicación inválida"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            parser = MassiveReceiptUploadExcelParser()
            parsed_rows = parser.parse(excel_file)
        except ValueError as error:
            return Response(
                {"message": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as error:
            logger.exception("Error leyendo Excel de recaudos")
            return Response(
                {"message": "No fue posible leer el archivo Excel"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not parsed_rows:
            return Response(
                {"message": "El archivo no contiene filas válidas"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        expected_by_operation = {
            str(item.get("preOperationId") or item.get("operation") or item.get("id")): item
            for item in expected_rows
            if item.get("preOperationId") or item.get("operation") or item.get("id")
        }

        operation_ids = [
            str(row.get("preOperationId") or row.get("operation") or "")
            for row in parsed_rows
            if row.get("preOperationId") or row.get("operation")
        ]

        preoperations = (
            PreOperation.objects
            .filter(id__in=operation_ids, status=1, state=1)
            .select_related("bill", "clientAccount")
        )

        preoperation_map = {
            str(op.id): op
            for op in preoperations
        }

        response_rows = []
        normalized_rows = []
        error_count = 0

        for index, parsed in enumerate(parsed_rows, start=1):
            row_errors = []

            operation_id = str(parsed.get("preOperationId") or parsed.get("operation") or "")
            expected = expected_by_operation.get(operation_id)
            op = preoperation_map.get(operation_id)

            if not operation_id:
                row_errors.append({
                    "field": "preOperationId",
                    "message": "La fila no contiene PREOPERACIÓN.",
                })

            if operation_id and operation_id not in expected_by_operation:
                row_errors.append({
                    "field": "operation_context",
                    "message": "La operación no pertenece al lote generado.",
                })

            if operation_id and not op:
                row_errors.append({
                    "field": "preOperationId",
                    "message": "Operación no encontrada o inactiva.",
                })

            excel_bill_number = str(parsed.get("billNumber") or "").strip()
            expected_bill_number = str((expected or {}).get("billNumber") or "").strip()

            if expected and expected_bill_number and excel_bill_number != expected_bill_number:
                row_errors.append({
                    "field": "billNumber",
                    "message": "La factura no coincide con el lote generado.",
                })

            try:
                payed_amount = money(parsed.get("payedAmount") or 0)
            except Exception:
                payed_amount = Decimal("0.00")
                row_errors.append({
                    "field": "payedAmount",
                    "message": "Monto aplicación inválido.",
                })

            if payed_amount <= Decimal("0.00"):
                row_errors.append({
                    "field": "payedAmount",
                    "message": "El monto aplicación debe ser mayor a cero.",
                })

            try:
                calculated_days = int(parsed.get("calculatedDays") or 0)
            except Exception:
                calculated_days = 0
                row_errors.append({
                    "field": "calculatedDays",
                    "message": "Días cálculo inválido.",
                })

            if calculated_days < 0:
                row_errors.append({
                    "field": "calculatedDays",
                    "message": "Días cálculo no puede ser negativo.",
                })

            preview_row = None

            if op and not row_errors:
                try:
                    preview_row = build_receipt_preview_row(
                        op,
                        application_date,
                        receipt_status_id=receipt_status_id,
                        payed_amount_override=payed_amount,
                    )

                    # El usuario puede modificar días cálculo en Excel.
                    # Si lo modifica, se guarda como calculatedDays.
                    preview_row["calculatedDays"] = calculated_days

                except ValueError as error:
                    row_errors.append({
                        "field": "operation",
                        "message": str(error),
                    })
                except Exception:
                    logger.exception("Error recalculando recaudo desde Excel")
                    row_errors.append({
                        "field": "operation",
                        "message": "No fue posible recalcular el recaudo.",
                    })

            has_errors = len(row_errors) > 0

            if has_errors:
                error_count += 1

            display_row = {
                "id": parsed.get("rowNumber") or index,
                "rowNumber": parsed.get("rowNumber") or index,
                "preOperationId": operation_id,
                "operation": operation_id,

                "billId": parsed.get("billId") or "",
                "billNumber": excel_bill_number,
                "fraction": parsed.get("fraction") or "",
                "opId": parsed.get("opId") or "",
                "investorName": (
                    preview_row.get("investorName")
                    if preview_row
                    else (expected or {}).get("investorName", "")
                ),

                "periodStart": (
                    preview_row.get("periodStart")
                    if preview_row
                    else parsed.get("periodStart")
                ),
                "periodEnd": (
                    preview_row.get("periodEnd")
                    if preview_row
                    else parsed.get("periodEnd")
                ),

                "futureValue": preview_row.get("futureValue") if preview_row else 0,
                "nominalValue": preview_row.get("nominalValue") if preview_row else 0,
                "pending": preview_row.get("pending") if preview_row else 0,
                "additionalDays": preview_row.get("additionalDays") if preview_row else 0,
                "interests": preview_row.get("interests") if preview_row else 0,
                "toCollect": preview_row.get("toCollect") if preview_row else 0,

                "payedAmount": float(payed_amount),
                "calculatedDays": calculated_days,
                "realDays": preview_row.get("realDays") if preview_row else 0,

                "receiptType": preview_row.get("receiptType") if preview_row else "",
                "typeReceipt": preview_row.get("typeReceipt") if preview_row else "",
                "receiptTypeLabel": (
                    get_receipt_label_from_type_id(preview_row.get("typeReceipt"))
                    if preview_row
                    else ""
                ),
                "receiptStatus": receipt_status_id,
                "statusKey": preview_row.get("statusKey") if preview_row else "",

                "errors": row_errors,
                "fieldErrors": build_field_errors(row_errors),
                "hasErrors": has_errors,
            }

            response_rows.append(display_row)

            if preview_row and not has_errors:
                normalized_rows.append({
                    **preview_row,
                    "rowNumber": parsed.get("rowNumber") or index,
                    "payedAmount": float(payed_amount),
                    "calculatedDays": calculated_days,
                    "receiptTypeLabel": get_receipt_label_from_type_id(preview_row.get("typeReceipt")),
                })

        can_register = error_count == 0 and len(normalized_rows) > 0

        return Response(
            {
                "success": can_register,
                "canRegister": can_register,
                "totalRows": len(response_rows),
                "processedRows": len(normalized_rows),
                "errorCount": error_count,
                "rows": response_rows,
                "normalizedRows": normalized_rows,
                "summary": build_receipt_summary_from_rows(normalized_rows),
                "message": (
                    f"Se han validado {len(normalized_rows)} recaudo(s)."
                    if can_register
                    else "El Excel contiene errores en los datos. Revise los valores resaltados."
                ),
            },
            status=status.HTTP_200_OK,
        )
class MassiveReceiptRegister(APIView):
    @transaction.atomic
    def post(self, request):
        application_date = request.data.get("applicationDate")
        receipt_status_id = request.data.get("receiptStatus")
        rows = request.data.get("rows") or request.data.get("operations") or []

        if not application_date:
            return Response(
                {"error": True, "message": "Se requiere applicationDate"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not receipt_status_id:
            return Response(
                {"error": True, "message": "Se requiere receiptStatus"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(rows, list) or len(rows) == 0:
            return Response(
                {"error": True, "message": "Se requieren filas para registrar"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        application_date = parse_date(application_date)

        preoperation_ids = [
            item.get("preOperationId") or item.get("id") or item.get("operation")
            for item in rows
            if item.get("preOperationId") or item.get("id") or item.get("operation")
        ]

        preoperations = (
            PreOperation.objects
            .filter(id__in=preoperation_ids, status=1, state=1)
            .select_related("bill", "clientAccount")
        )

        preoperation_map = {
            str(op.id): op
            for op in preoperations
        }

        created = []
        errors = []

        for item in rows:
            op_id = str(
                item.get("preOperationId")
                or item.get("id")
                or item.get("operation")
                or ""
            )

            op = preoperation_map.get(op_id)

            if not op:
                errors.append({
                    "operation": op_id,
                    "message": "Operación no encontrada o inactiva",
                })
                continue
            
            try:
                payed_amount = money(item.get("payedAmount") or 0)
            except Exception:
                errors.append({
                    "operation": op_id,
                    "message": "Monto aplicación inválido",
                })
                continue

            if payed_amount <= Decimal("0.00"):
                errors.append({
                    "operation": op_id,
                    "message": "El monto aplicación debe ser mayor a cero",
                })
                continue
            preview_row = build_receipt_preview_row(
                op,
                application_date,
                receipt_status_id=receipt_status_id,
                payed_amount_override=payed_amount,
            )
            if item.get("calculatedDays") not in [None, ""]:
                try:
                    preview_row["calculatedDays"] = int(item.get("calculatedDays"))
                except Exception:
                    errors.append({
                        "operation": op_id,
                        "message": "Días cálculo inválido",
                    })
                    continue
            if not preview_row:
                errors.append({
                    "operation": op_id,
                    "message": "No se pudo calcular el recaudo",
                })
                continue

            if not preview_row.get("account"):
                errors.append({
                    "operation": op_id,
                    "message": "La operación no tiene cuenta de inversionista asociada",
                })
                continue

            payload = {
                "date": application_date,
                "typeReceipt": preview_row["typeReceipt"],
                "receiptStatus": receipt_status_id,

                "payedAmount": preview_row["payedAmount"],
                "opPendingAmount": preview_row["pending"],
                "operation": preview_row["operation"],
                "account": preview_row["account"],

                "additionalDays": preview_row["additionalDays"],
                "additionalInterests": preview_row["additionalInterests"],
                "additionalInterestsSM": preview_row["additionalInterestsSM"],
                "investorInterests": preview_row["investorInterests"],
                "tableInterests": preview_row["tableInterests"],
                "futureValueRecalculation": preview_row["futureValueRecalculation"],
                "tableRemaining": preview_row["tableRemaining"],
                "realDays": preview_row["realDays"],
                "remaining": preview_row["remaining"],
                "calculatedDays": preview_row["calculatedDays"],
                "presentValueInvestor": preview_row["presentValueInvestor"],

                "client": preview_row.get("payerId") or None,
                "user_created_at": getattr(request.user, "id", None),
            }

            serializer = ReceiptSerializer(
                data=payload,
                context={"request": request},
            )

            if serializer.is_valid():
                receipt = serializer.save()
                created.append(serializer.data)
            else:
                errors.append({
                    "operation": op_id,
                    "billId": preview_row.get("billId"),
                    "message": serializer.errors,
                })

        if errors:
            transaction.set_rollback(True)
            return Response(
                {
                    "error": True,
                    "message": "Algunos recaudos no pudieron registrarse",
                    "errors": errors,
                    "createdCount": len(created),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "error": False,
                "message": "Recaudos registrados correctamente",
                "createdCount": len(created),
                "data": created,
            },
            status=status.HTTP_200_OK,
        )

class ReceiptAV(BaseAV):

    @checkRole(['admin'])
    def get(self, request, pk=None):
        try:
            
            if len(request.query_params) > 0:
                
                if request.query_params.get('id') != '' and len(request.query_params) == 1: #and request.query_params.get('opId_billId') in [None, ''] and request.query_params.get('statusReceipt') in [None, ''] and request.query_params.get('startDate') in [None, ''] and request.query_params.get('endDate') in [None, '']:
                
                    receipts    = Receipt.objects.filter(id=request.query_params.get('id'))
                    page        = self.paginate_queryset(receipts)
                    if page is not None:
                        serializer = ReceiptReadOnlySerializer(page, many=True)
                        return self.get_paginated_response(serializer.data)
                
                elif request.query_params.get('opId') != '' and len(request.query_params) == 2: #and request.query_params.get('opId_billId') in [None, ''] and request.query_params.get('statusReceipt') in [None, ''] and request.query_params.get('startDate') in [None, ''] and request.query_params.get('endDate') in [None, '']:
              
                    receipts    = Receipt.objects.filter(operation__opId=request.query_params.get('opId'))
                    page        = self.paginate_queryset(receipts)
                    if page is not None:
                        serializer = ReceiptReadOnlySerializer(page, many=True)
                        return self.get_paginated_response(serializer.data)
               

                elif request.query_params.get('opId_billId') not in [None, ''] and request.query_params.get('statusReceipt') in [None, ''] and request.query_params.get('startDate') in [None, ''] and request.query_params.get('endDate') in [None, '']:
                    try:
                        search_value = request.query_params.get('opId_billId', '').strip()
                        
                        
                        # Intentar buscar como opId (numérico)
                        try:
                            op_id_value = int(search_value)
                            receipts_by_opid = Receipt.objects.filter(operation__opId=op_id_value)
                        except (ValueError, TypeError):
                            receipts_by_opid = Receipt.objects.none()
                        
                        # Buscar como billId (texto)
                        receipts_by_billid = Receipt.objects.filter(operation__bill__billId=search_value)
                        
                        # Combinar resultados
                        receipts = receipts_by_opid | receipts_by_billid
                        
                        page = self.paginate_queryset(receipts)
                        if page is not None:
                            serializer = ReceiptReadOnlySerializer(page, many=True)
                            return self.get_paginated_response(serializer.data)
                            
                    except Exception as e:
                        logger.error(f"Error filtering receipts: {str(e)}")
                     
                     
                elif request.query_params.get('opId_billId') != '' and request.query_params.get('statusReceipt')!='' and request.query_params.get('startDate')=='' and request.query_params.get('endDate')=='':
                    try:
                        search_value = request.query_params.get('opId_billId', '').strip()
                        
                        # Intentar buscar como opId (numérico)
                        try:
                            op_id_value = int(search_value)
                            receipts_by_opid = Receipt.objects.filter(operation__opId=op_id_value,
                                                         typeReceipt_id=request.query_params.get('statusReceipt'))
                        except (ValueError, TypeError):
                            receipts_by_opid = Receipt.objects.none()
                        
                        # Buscar como billId (texto)
                        receipts_by_billid = Receipt.objects.filter(operation__bill__billId=search_value,
                                                         typeReceipt_id=request.query_params.get('statusReceipt'))
                        
                        # Combinar resultados
                        receipts = receipts_by_opid | receipts_by_billid
                        
                        page = self.paginate_queryset(receipts)
                        if page is not None:
                            serializer = ReceiptReadOnlySerializer(page, many=True)
                            return self.get_paginated_response(serializer.data)
                            
                    except Exception as e:
                        logger.error(f"Error filtering receipts: {str(e)}")
                elif request.query_params.get('opId_billId') != '' and request.query_params.get('statusReceipt')!='' and request.query_params.get('startDate')!='' and request.query_params.get('endDate')!='':
                    try:
                        search_value = request.query_params.get('opId_billId', '').strip()
                        
                        
                        # Intentar buscar como opId (numérico)
                        try:
                            op_id_value = int(search_value)
                            receipts_by_opid = Receipt.objects.filter(operation__opId=op_id_value,
                                                        date__gte=request.query_params.get('startDate'),
                                                        date__lte=request.query_params.get('endDate'),
                                                        typeReceipt_id=request.query_params.get('statusReceipt'))
                        except (ValueError, TypeError):
                            receipts_by_opid = Receipt.objects.none()
                        
                        # Buscar como billId (texto)
                        receipts_by_billid = Receipt.objects.filter(operation__bill__billId=search_value,
                                                        date__gte=request.query_params.get('startDate'),
                                                        date__lte=request.query_params.get('endDate'),
                                                        typeReceipt_id=request.query_params.get('statusReceipt'))
                        
                        # Combinar resultados
                        receipts = receipts_by_opid | receipts_by_billid
                        
                        page = self.paginate_queryset(receipts)
                        if page is not None:
                            serializer = ReceiptReadOnlySerializer(page, many=True)
                            return self.get_paginated_response(serializer.data)
                            
                    except Exception as e:
                        logger.error(f"Error filtering receipts: {str(e)}")
                elif request.query_params.get('opId_billId') != '' and request.query_params.get('statusReceipt')=='' and request.query_params.get('startDate')!='' and request.query_params.get('endDate')!='':
                    try:
                        search_value = request.query_params.get('opId_billId', '').strip()
                        
                        
                        # Intentar buscar como opId (numérico)
                        try:
                            op_id_value = int(search_value)
                            receipts_by_opid = Receipt.objects.filter(operation__opId=op_id_value,
                                                        date__gte=request.query_params.get('startDate'),
                                                        date__lte=request.query_params.get('endDate'),
                                                        )
                        except (ValueError, TypeError):
                            receipts_by_opid = Receipt.objects.none()
                        
                        # Buscar como billId (texto)
                        receipts_by_billid = Receipt.objects.filter(operation__bill__billId=search_value,
                                                        date__gte=request.query_params.get('startDate'),
                                                        date__lte=request.query_params.get('endDate'),
                                                        )
                        
                        # Combinar resultados
                        receipts = receipts_by_opid | receipts_by_billid
                        
                        page = self.paginate_queryset(receipts)
                        if page is not None:
                            serializer = ReceiptReadOnlySerializer(page, many=True)
                            return self.get_paginated_response(serializer.data)
                            
                    except Exception as e:
                        logger.error(f"Error filtering receipts: {str(e)}")
                elif request.query_params.get('opId_billId') == '' and request.query_params.get('statusReceipt')!='' and request.query_params.get('startDate')!='' and request.query_params.get('endDate')!='':
                    
                    receipts    = Receipt.objects.filter(
                                                         date__gte=request.query_params.get('startDate'),
                                                            date__lte=request.query_params.get('endDate'),
                                                            typeReceipt_id=request.query_params.get('statusReceipt'))
                    page        = self.paginate_queryset(receipts)
                    if page is not None:
                        serializer = ReceiptReadOnlySerializer(page, many=True)
                        return self.get_paginated_response(serializer.data)
                elif request.query_params.get('opId_billId') == '' and request.query_params.get('statusReceipt')=='' and request.query_params.get('startDate')!='' and request.query_params.get('endDate')!='':
                    
                    receipts    = Receipt.objects.filter(date__gte=request.query_params.get('startDate'),
                                                        date__lte=request.query_params.get('endDate'))
                    page        = self.paginate_queryset(receipts)
                    if page is not None:
                        serializer = ReceiptReadOnlySerializer(page, many=True)
                        return self.get_paginated_response(serializer.data)
                elif request.query_params.get('opId_billId') == '' and request.query_params.get('statusReceipt')!='' and request.query_params.get('startDate')=='' and request.query_params.get('endDate')=='':
                    
                    receipts    = Receipt.objects.filter(typeReceipt_id=request.query_params.get('statusReceipt'))
                    page        = self.paginate_queryset(receipts)
                    if page is not None:
                        serializer = ReceiptReadOnlySerializer(page, many=True)
                        return self.get_paginated_response(serializer.data)    
                else:
                    receipts    = Receipt.objects.filter(state=1)
                    page        = self.paginate_queryset(receipts)
                    if page is not None:
                        serializer = ReceiptReadOnlySerializer(page, many=True)
                        return self.get_paginated_response(serializer.data)


            if pk:
                receipt      = Receipt.objects.get(pk=pk)
                serializer   = ReceiptSerializer(receipt)
                return response({'error': False, 'data': serializer.data}, 200)
        except Receipt.DoesNotExist:
            return response({'error': True, 'message': 'recaudo/s no encontrados'}, 500)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['admin'])
    def post(self, request):
        try:
            serializer = ReceiptSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'message': 'Recaudo creado','data': serializer.data}, 200)
            else:
                return response({'error': True, 'message': serializer.errors}, 400)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['admin'])
    def patch(self, request, pk):
        try:
            receipt     = Receipt.objects.get(pk=pk)
            serializer  = ReceiptSerializer(receipt, data=request.data, context={'request': request}, partial=True)
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'message': 'Recaudo actualizado', 'data': serializer.data}, 200)
            return response({'error': True, 'message': serializer.errors}, 400)
        except Receipt.DoesNotExist:
            return response({'error': True, 'message': 'Recaudo no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
    @checkRole(['admin'])
    def delete(self, request, pk):
        try:
            receipt       = Receipt.objects.get(pk=pk)
            # update the state of the operation
            receipt.operation.amount          -= receipt.investorInterests
            receipt.operation.opPendingAmount -= receipt.investorInterests
            receipt.operation.amount          -= receipt.additionalInterests
            receipt.operation.opPendingAmount -= receipt.additionalInterests
            receipt.operation.amount          -= receipt.tableInterests
            receipt.operation.opPendingAmount -= receipt.tableInterests
            receipt.operation.payedAmount     -= receipt.payedAmount
            receipt.state = 0
            receipt.operation.save()
            receipt.save()
            return response({'error': False, 'message': 'Recaudo eliminado'}, 200)
        except Receipt.DoesNotExist:
            return response({'error': True, 'message': 'Recaudo no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)


