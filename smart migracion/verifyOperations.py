import pandas as pd
import uuid
import json
from datetime import datetime
# Read the tablas.xlsx file and get the CORREDORES sheet
df = pd.read_excel('newTables.xlsx', sheet_name='BASE')
# convert all rows to a list of dictionaries
data = df.to_dict('records')

operations = []

for row in data:
    requiredOpIds = [338,343,474,1131,277,276,275,1019,293]
    # ignore the row if it is not an operation
    if row['TIPO_OP'] == 'COMPRA TITULO':
        opId           = row['NRO_OP']
        billId         = row['NRO_FACT_OP']
        billFraction   = row['FRAC_FACT_OP']
        amount         = row['VALOR_FUT_FACT_OP']
        payedAmount    = row['VALOR_NOM_FACT_OP']
        emitter        = row['ID_EMISOR_OP']
        emitterName    = row['NOMBRE_EMISOR_OP']
        payer          = row['ID_PAGADOR_OP']
        payerName      = row['NOMBRE_PAGADOR_OP']
        investor       = row['ID_INVERSIONISTA_OP']
        investorName   = row['NOMBRE_INVERSIONISTA_OP']
        clientAccount  = row['CUENTA_INVERSIONISTA_OP']
        applyGM        = True if row['GMF_OP'] == -1 else False
        presentValueSF = row['VA_PRESENTE_SM'] * -1
        investorProfit = row['UTILIDAD_INV']
        commissionSF   = row['COMISION_SM']

        # check the receipt type 
        if row['TIPO_RECAUDO'] == 'RECOMPRA':
            isBillReBuy = True
        else:
            isBillReBuy = False

        if row['TIPO_OP2'] == 'RECOMPRA':
            reBuyOperation = True
        else:
            reBuyOperation = False

        if row['ESTADO1'] == 'CANCELADO':
            isCanceled = True
        else:
            isCanceled = False

        # check the operation state
        #if row['ESTADO1'] == 'CANCELADO':
        #    print(row['NRO_OP'], row['NRO_FACT_OP'], row['FRAC_FACT_OP'],isReBuy, row['VALOR_FUT_FACT_OP'], row['VALOR_NOM_FACT_OP'], row['ID_EMISOR_OP'], row['ID_PAGADOR_OP'], row['ID_INVERSIONISTA_OP'], row['CUENTA_INVERSIONISTA_OP'])
        if row['NRO_OP'] in requiredOpIds:
            operations.append({
                'opId': row['NRO_OP'],
                'billId': row['NRO_FACT_OP'],
                'billFraction': row['FRAC_FACT_OP'],
                'isBillReBuy': isBillReBuy,
                'reBuyOperation': reBuyOperation,
                'amount': row['VALOR_FUT_FACT_OP'],
                'payedAmount': row['VALOR_NOM_FACT_OP'],
                'emitter': row['ID_EMISOR_OP'],
                'emitterName': row['NOMBRE_EMISOR_OP'],
                'payer': row['ID_PAGADOR_OP'],
                'payerName': row['NOMBRE_PAGADOR_OP'],
                'investor': row['ID_INVERSIONISTA_OP'],
                'investorName': row['NOMBRE_INVERSIONISTA_OP'],
                'clientAccount': row['CUENTA_INVERSIONISTA_OP'],
                'isCanceled': isCanceled,
                'applyGM': applyGM,
                'presentValueSF': presentValueSF,
                'investorProfit': investorProfit,
                'commissionSF': commissionSF
            })

# write the operations to a json file
with open('verifyOperations.json', 'w') as outfile:
    json.dump(operations, outfile, indent=4)
    