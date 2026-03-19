class UploadExcelResponseBuilder:
    def build(self, validated_rows):
        error_count = sum(1 for row in validated_rows if row["has_errors"])
        can_register = error_count == 0 and len(validated_rows) > 0

        rows = []
        normalized_rows = []

        for row in validated_rows:
            calc = row.get("calculated_payload") or {}

            rows.append({
                "id": row["row_number"],
                "rowId": row["row_number"],
                "facturaId": row.get("bill_number") or "",
                "emisor": row.get("emitter_name") or "",
                "inversionista": row.get("investor_name") or "",
                "pagador": row.get("payer_name") or "",
                "tasaDesc": row.get("tasa_descuento"),
                "tasaInv": row.get("tasa_inversionista"),
                "valorFuturo": row.get("valor_futuro"),
                "valorNominal": calc.get("valorNominal"),
                "valorInversionista": calc.get("presentValueInvestor"),
                "fechaProbable": row.get("fecha_probable"),
                "fechaFin": row.get("fecha_fin"),
                "applyGm": calc.get("applyGm", False),
                "gmValue": calc.get("GM", 0),
                "fieldErrors": row.get("field_errors", {}),
                "errors": row.get("errors", []),
                "hasErrors": row.get("has_errors", False),
            })

            normalized_rows.append({
                "rowNumber": row["row_number"],
                "opId": row.get("op_id"),
                "opDate": row.get("op_date").isoformat() if row.get("op_date") else None,
                "emitterId": row.get("emitter_id"),
                "payerId": row.get("payer_id"),
                "investorId": row.get("investor_id"),
                "billId": row.get("bill_id"),
                "billFraction": row.get("bill_fraction"),
                "clientAccountNumber": row.get("investor_account"),
                "emitterBrokerId": row.get("emitter_broker_id"),
                "investorBrokerId": calc.get("investorBrokerId"),
                "fechaProbable": row.get("fecha_probable").isoformat() if row.get("fecha_probable") else None,
                "fechaFin": row.get("fecha_fin").isoformat() if row.get("fecha_fin") else None,
                "valorFuturo": row.get("valor_futuro"),
                "porcentajeDescuento": row.get("porcentaje_descuento"),
                "tasaDescuento": row.get("tasa_descuento"),
                "tasaInversionista": row.get("tasa_inversionista"),
                "calculated": calc,
                "applyGm": calc.get("applyGm", False),
                "gmValue": calc.get("GM", 0),
                "hasErrors": row.get("has_errors", False),
                "errors": row.get("errors", []),
            })

        return {
            "success": can_register,
            "canRegister": can_register,
            "processedRows": len(validated_rows),
            "errorCount": error_count,
            "operationId": validated_rows[0].get("op_id") if validated_rows else None,
            "rows": rows,
            "normalizedRows": normalized_rows,
        }