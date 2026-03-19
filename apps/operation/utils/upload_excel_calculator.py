from math import pow
import logging

logger = logging.getLogger(__name__)


class UploadExcelCalculator:
    GM_RATE = 0.002

    @staticmethod
    def percent_to_decimal(value):
        if value is None:
            return None
        return value / 100.0

    def calculate(self, row, apply_gm=False):
        porcentaje_desc = self.percent_to_decimal(row["porcentaje_descuento"])
        tasa_desc = self.percent_to_decimal(row["tasa_descuento"])
        tasa_inv = self.percent_to_decimal(row["tasa_inversionista"])

        valor_futuro = row["valor_futuro"]
        op_date = row["op_date"]
        fecha_fin = row["fecha_fin"]

        operation_days = (fecha_fin - op_date).days
        valor_nominal = valor_futuro * porcentaje_desc

        present_value_sf = valor_nominal / pow(1 + tasa_desc, operation_days / 365)
        present_value_investor = valor_nominal / pow(1 + tasa_inv, operation_days / 365)

        investor_profit = valor_nominal - present_value_investor
        commission_sf = present_value_investor - present_value_sf
        gm = present_value_investor * self.GM_RATE if apply_gm else 0

        payload = {
            "valorNominal": round(valor_nominal, 2),
            "operationDays": operation_days,
            "presentValueSF": round(present_value_sf, 2),
            "presentValueInvestor": round(present_value_investor, 2),
            "investorProfit": round(investor_profit, 2),
            "commissionSF": round(commission_sf, 2),
            "GM": round(gm, 2),
            "opExpiration": fecha_fin,
        }

        logger.debug(payload)
        return payload