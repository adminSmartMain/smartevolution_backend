import pandas as pd
import uuid
import json
from datetime import datetime
# Read the tablas.xlsx file and get the CORREDORES sheet
df = pd.read_excel('newTables.xlsx', sheet_name='RESUMEN NEGOCIACION')
# convert all rows to a list of dictionaries
data = df.to_dict('records')

receipts = []

for row in data:
    id = str(uuid.uuid4())
    opId = row['NRO_OP']
    date = str(row['FECHA'])
    # delete the  00:00:00 from the str
    date = date[:10]
    emitter = row['EMISOR_RNEG']
    payer   = row['PAGADOR_RNEG']
    emitterId = row['ID_EMISOR_RNEG']
    payerId   = row['ID_PAGADOR_RNEG']
    futureValue = row['VF_RNEG']
    payedPercent= "Ver Reporte de compra"
    valueToDiscount = row['VF_RNEG']
    discountTax = row['TASA_DESC'] * 100
    discountedDays = "Ver Reporte de compra"
    smDiscount = row['VAL_DESC_SMART']
    investorValue = row['VALOR_VENTA_INV']
    investorDiscount = row['DESC_PRONTO_PAGO']
    commissionValueBeforeTaxes = 0
    operationValue = row['COSTO_OP']
    tableCommission = row['COMISION_MESA']
    iva = row['IVA']
    retIva = row['RETENCION_IVA']
    retIca = row['ICA']
    retFte = row['RETENCION']
    billId = row['COD_CONT']
    billValue = row['VAL_FACT']
    totalDiscounts = row['TOTAL_DESC_NEG']
    totalDeposits = row['TOTAL_CONSIG_NEG']
    total = row['TOTAL_DESEMBOLSAR']
    pendingToDeposit = row['PENDIENTE_DESEMB']
    observations = row['OBSERVACIONES'] if row['OBSERVACIONES'] else ''

    receipt = {
        'id': id,
        'opId': opId,
        'date': date,
        'emitter': emitter,
        'payer': payer,
        'emitterId': emitterId,
        'payerId': payerId,
        'futureValue': futureValue,
        'payedPercent': payedPercent,
        'valueToDiscount': valueToDiscount,
        'discountTax': discountTax,
        'discountedDays': discountedDays,
        'SMDiscount': smDiscount,
        'investorValue': investorValue,
        'investorDiscount': investorDiscount,
        'commissionValueBeforeTaxes': commissionValueBeforeTaxes,
        'operationValue': operationValue,
        'tableCommission': tableCommission,
        'iva': iva,
        'retIva': retIva,
        'retIca': retIca,
        'retFte': retFte,
        'billId': billId,
        'billValue':billValue,
        'totalDiscounts': totalDiscounts,
        'totalDeposits': totalDeposits,
        'total': total,
        'pendingToDeposit': pendingToDeposit,
        'observations': observations
    }

    receipts.append(receipt)


# convert the list of dictionaries to a json file
with open('receipts.json', 'w') as f:
    json.dump(receipts, f, indent=4)

            