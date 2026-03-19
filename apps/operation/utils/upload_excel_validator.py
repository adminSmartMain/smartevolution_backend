from collections import defaultdict


class UploadExcelValidator:
    REQUIRED_FIELDS = [
        "op_id",
        "op_date",
        "emitter_name",
        "emitter_id",
        "emitter_broker_name",
        "emitter_broker_id",
        "payer_name",
        "payer_id",
        "bill_number",
        "bill_id",
        "bill_balance",
        "bill_fraction",
        "investor_name",
        "investor_id",
        "investor_account",
        "fecha_probable",
        "fecha_fin",
        "valor_futuro",
        "porcentaje_descuento",
        "tasa_descuento",
        "tasa_inversionista",
    ]

    CALC_REQUIRED_FIELDS = [
        "valor_futuro",
        "porcentaje_descuento",
        "tasa_descuento",
        "tasa_inversionista",
        "op_date",
        "fecha_fin",
    ]

    def __init__(self, references, calculator):
        self.references = references
        self.calculator = calculator

    def validate_rows(self, parsed_rows):
        grouped_by_bill = defaultdict(list)
        for row in parsed_rows:
            bill_id = str(row.get("bill_id")) if row.get("bill_id") else None
            if bill_id:
                grouped_by_bill[bill_id].append(row)

        validated = []

        for row in parsed_rows:
            field_errors = {}
            errors = []

            def add_error(field, message):
                field_errors[field] = True
                errors.append({"field": field, "message": message})

            for field in self.REQUIRED_FIELDS:
                if row.get(field) in [None, ""]:
                    add_error(field, "Este campo es obligatorio")

            emitter = self.references["clients_by_id"].get(str(row.get("emitter_id")))
            payer = self.references["clients_by_id"].get(str(row.get("payer_id")))
            investor = self.references["clients_by_id"].get(str(row.get("investor_id")))
            bill = self.references["bills_by_id"].get(str(row.get("bill_id")))
            emitter_broker = self.references["brokers_by_id"].get(str(row.get("emitter_broker_id")))
            account = self.references["accounts_by_number"].get(str(row.get("investor_account")).strip())
            risk_profile = self.references["risk_profile_by_client_id"].get(str(row.get("investor_id")))
            investor_broker_info = self.references["investor_broker_by_investor_id"].get(
                str(row.get("investor_id")),
                {},
            )

            if row.get("emitter_id") and not emitter:
                add_error("emitter_id", "El emisor no existe")

            if row.get("payer_id") and not payer:
                add_error("payer_id", "El pagador no existe")

            if row.get("investor_id") and not investor:
                add_error("investor_id", "El inversionista no existe")

            if row.get("bill_id") and not bill:
                add_error("bill_id", "La factura no existe")

            if row.get("emitter_broker_id") and not emitter_broker:
                add_error("emitter_broker_id", "El corredor del emisor no existe")

            if row.get("investor_account") and not account:
                add_error("investor_account", "La cuenta del inversionista no existe")

            if investor and account and str(getattr(account, "client_id", "")) != str(investor.id):
                add_error("investor_account", "La cuenta no pertenece al inversionista")

            if investor and not investor_broker_info.get("broker_id"):
                add_error("investor_id", "El inversionista no tiene corredor asociado")

            if bill and emitter and hasattr(bill, "emitter_id"):
                if str(bill.emitter_id) != str(emitter.id):
                    add_error("bill_id", "La factura no pertenece al emisor")

            if bill and payer and hasattr(bill, "payer_id"):
                if str(bill.payer_id) != str(payer.id):
                    add_error("bill_id", "La factura no pertenece al pagador")

            bill_id = str(row.get("bill_id")) if row.get("bill_id") else None
            if bill_id and row.get("bill_fraction") is not None:
                grouped_rows = sorted(
                    grouped_by_bill[bill_id],
                    key=lambda x: x.get("bill_fraction") or 0
                )

                expected_start = self.references["next_fraction_by_bill"].get(bill_id, 0)
                if expected_start == 0:
                    expected_start = 1

                expected_sequence = list(range(expected_start, expected_start + len(grouped_rows)))
                actual_sequence = [r.get("bill_fraction") for r in grouped_rows]

                if actual_sequence != expected_sequence:
                    add_error(
                        "bill_fraction",
                        f"Las fracciones deben ser consecutivas: {expected_sequence}"
                    )

            valor_futuro = row.get("valor_futuro")
            bill_balance = row.get("bill_balance")

            if valor_futuro is not None and bill_balance is not None:
                if valor_futuro <= 0:
                    add_error("valor_futuro", "El valor futuro debe ser mayor a 0")
                if valor_futuro > bill_balance:
                    add_error("valor_futuro", "El valor futuro no puede ser mayor al saldo")

            if bill_id:
                total_future = sum((r.get("valor_futuro") or 0) for r in grouped_by_bill[bill_id])
                current_balance = row.get("bill_balance") or 0
                if total_future > current_balance:
                    add_error(
                        "valor_futuro",
                        "La suma del valor futuro de las fracciones no puede superar el saldo"
                    )

            porcentaje_descuento = row.get("porcentaje_descuento")
            if porcentaje_descuento is not None:
                if porcentaje_descuento <= 0:
                    add_error("porcentaje_descuento", "El % descuento debe ser mayor a 0")
                if porcentaje_descuento > 100:
                    add_error("porcentaje_descuento", "El % descuento no puede ser mayor a 100")

            tasa_desc = row.get("tasa_descuento")
            tasa_inv = row.get("tasa_inversionista")
            if tasa_desc is not None and tasa_inv is not None:
                if tasa_desc < tasa_inv:
                    add_error(
                        "tasa_descuento",
                        "La tasa de descuento no puede ser menor a la tasa inversionista"
                    )

            fecha_probable = row.get("fecha_probable")
            fecha_fin = row.get("fecha_fin")
            op_date = row.get("op_date")

            if fecha_probable and op_date and fecha_probable < op_date:
                add_error(
                    "fecha_probable",
                    "La fecha probable no puede ser menor a la fecha de operación"
                )

            if fecha_fin and fecha_probable and fecha_fin < fecha_probable:
                add_error(
                    "fecha_fin",
                    "La fecha fin no puede ser menor a la fecha probable"
                )

            calculated_payload = {}
            can_calculate = all(row.get(field) not in [None, ""] for field in self.CALC_REQUIRED_FIELDS)

            if can_calculate:
                try:
                    # SOLO DESDE PERFIL DE RIESGO DEL INVERSIONISTA
                    apply_gm = bool(getattr(risk_profile, "gmf", False)) if risk_profile else False

                    calculated_payload = self.calculator.calculate(row, apply_gm=apply_gm)
                    calculated_payload["applyGm"] = apply_gm

                    valor_nominal = calculated_payload.get("valorNominal")
                    if valor_nominal is not None and valor_futuro is not None and valor_nominal > valor_futuro:
                        add_error(
                            "valor_nominal",
                            "El valor nominal no puede ser mayor al valor futuro"
                        )

                    if account:
                        required_balance = (
                            calculated_payload.get("presentValueInvestor", 0) +
                            calculated_payload.get("GM", 0)
                        )
                        account_balance = float(getattr(account, "balance", 0) or 0)
                        calculated_payload["insufficientAccountBalance"] = required_balance > account_balance
                        calculated_payload["accountBalance"] = account_balance

                    calculated_payload["investorBrokerId"] = investor_broker_info.get("broker_id")
                    calculated_payload["investorBrokerName"] = investor_broker_info.get("broker_name", "")

                except Exception as exc:
                    add_error("calculation", f"No se pudo calcular la fila: {str(exc)}")

            validated.append({
                **row,
                "field_errors": field_errors,
                "errors": errors,
                "has_errors": len(errors) > 0,
                "calculated_payload": calculated_payload,
            })

        return validated