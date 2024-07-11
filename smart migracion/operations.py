import pandas as pd
import uuid
import json
from datetime import datetime
import math
# Read the tablas.xlsx file and get the CORREDORES sheet
df = pd.read_excel('newTables.xlsx', sheet_name='BASE')
# convert all rows to a list of dictionaries
data = df.to_dict('records')

operations = []

for row in data:
    # ignore the row if it is not an operation
    if row['TIPO_OP'] == 'COMPRA TITULO':
        opId                 = row['NRO_OP']
        OpDate               = str(row['FECHA_RAD_OP'])
        # delete the  00:00:00 from the str 
        OpDate               = OpDate[:10]
        applyGM              = True if row['GMF_OP'] == -1 else False
        typeOP               = row['TIPO_OP']
        bill                 = row['NRO_FACT_OP']
        emitter              = row['ID_EMISOR_OP']
        emitterName          = row['NOMBRE_EMISOR_OP']
        payer                = row['ID_PAGADOR_OP']
        payerName            = row['NOMBRE_PAGADOR_OP']
        investor             = row['ID_INVERSIONISTA_OP']
        investorName         = row['NOMBRE_INVERSIONISTA_OP']
        dateBill             = str(row['FECHA_EMISION_FACT']) if row['FECHA_EMISION_FACT'] else str(row['FECHA_RAD_OP'])
        # delete the  00:00:00 from the str
        dateBill             = dateBill[:10]
        probableDate         = str(row['FECHA_PROB_OP'])
        # delete the  00:00:00 from the str
        probableDate         = probableDate[:10]
        expirationDate       = str(row['FECHA_FIN_OP'])
        # delete the  00:00:00 from the str
        expirationDate       = expirationDate[:10]
        discountTax          = row['TASA_DESC_OP'] if row['TASA_DESC_OP'] > 1 else row['TASA_DESC_OP'] * 100  
        investorTax          = row['TASA_INV_OP']  if row['TASA_INV_OP'] > 1  else row['TASA_INV_OP'] * 100  
        amount               = row['VALOR_FUT_FACT_OP'] 
        payedAmount          = row['VALOR_NOM_FACT_OP']
        payedPercent         = row['PORC_DESC_OP'] 
        operationDays        = row['DIAS_OP']
        presentValueInvestor = row['VA_PRESENTE_INV'] * -1
        presentValueSF       = row['VA_PRESENTE_SM'] * -1
        investorProfit       = row['UTILIDAD_INV']
        commissionSF        = row['COMISION_SM']
        gm                   = 0
        additionalInterests  = 0
        investorInterests    = 0
        tableInterests       = 0
        opExpiration         = str(row['FECHA_FIN_OP'])
        # delete the  00:00:00 from the str
        opExpiration         = opExpiration[:10]
        clientAccount        = row['CUENTA_INVERSIONISTA_OP']
        emitterBroker        = row['ID_CORR_V_OP']
        emitterBrokerName    = row['NOMBRE_CORR_V_OP']
        investorBroker       = row['ID_CORR_C_OP']
        investorBrokerName   = row['NOMBRE_CORR_C_OP']
        billFraction         = row['FRAC_FACT_OP']
        gm                   = row['GMV_VALOR']
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

        try:
            if math.isnan(billFraction):
                billFraction = 0
            else:
                pass
        except:
            billFraction = 0

        try:
            if math.isnan(gm):
                gm = 0
            else:
                pass
        except:
            gm = 0

        if gm != 0 or gm != 0.0:
            operations.append({
                'opId': opId,
                'OpDate': OpDate,
                'applyGM': applyGM,
                'typeOP': typeOP,
                'bill': bill,
                'emitter': emitter,
                'emitterName': emitterName,
                'payer': payer,
                'payerName': payerName,
                'investor': investor,
                'investorName': investorName,
                'dateBill': dateBill,
                'probableDate': probableDate,
                'expirationDate': expirationDate,
                'discountTax': discountTax,
                'investorTax': investorTax,
                'amount': amount,
                'payedAmount': payedAmount,
                'operationDays': operationDays,
                'gm': gm,
                'opExpiration': opExpiration,
                'clientAccount': clientAccount,
                'billFraction': billFraction,
    
            })


    #elif row['TIPO_OP'] == 'INTERESES ADICIONALES':
    #    # get the operation by the bill the investor and the opId using the operations list and a lambda function
    #    operation = list(filter(lambda op: op['bill'] == row['NRO_FACT_OP'] and op['investor'] == row['ID_INVERSIONISTA_OP'] and op['opId'] == row['NRO_OP'], operations))
    #    if len(operation) > 0:
    #        operation = operation[0]
    #        operation['additionalInterests'] = row['VA_PRESENTE_INV']
    #elif row['TIPO_OP'] == 'GM':
    #    if row['NRO_OP'] == 0:
    #        continue
    #    else:
    #        operation = list(filter(lambda op: op['bill'] == row['NRO_FACT_OP'] and op['investor'] == row['ID_INVERSIONISTA_OP'] and op['opId'] == row['NRO_OP'], operations))
    #        if len(operation) > 0:
    #            operation = operation[0]
    #            operation['GM'] = row['VA_PRESENTE_INV'] * -1
    
    

# save the operations in a json
with open('operations.json', 'w') as f:
    json.dump(operations, f, indent=4)
