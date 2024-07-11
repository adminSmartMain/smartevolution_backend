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
counter = 0
for row in data:
    # ignore the row if it is not an operation
    if row['TIPO_OP'] == 'RECAUDO TITULO':
        counter += 1

        id = str(uuid.uuid4())
        typeReceipt   = 'db1d1fa4-e467-4fde-9aee-bbf4008d688b'
        if row['TIPO_RECAUDO'] == 'TRANSFERENCIA':
            receiptStatus = '3db5ba64-0cf8-485a-afcf-5b17bad5784d'
        elif row['TIPO_RECAUDO'] == 'COMPENSACIÓN':
            receiptStatus = 'c5a11a9a-35b4-488f-929f-7fe23e80c311'
        elif row['TIPO_RECAUDO'] == 'RECOMPRA':
            receiptStatus = 'ea8518e8-168a-46d7-b56a-1286bf0037cd'
        else:
            receiptStatus = '3db5ba64-0cf8-485a-afcf-5b17bad5784d'

        # check if the date is NaT
        if pd.isnull(row['FECHA_APLICACION']) == False:
            date = str(row['FECHA_APLICACION'])
            # delete the  00:00:00 from the str 
            date = date[:10]
        else:
            date = str(row['FECHA_RAD_OP'])
            # delete the  00:00:00 from the str 
            date = date[:10]

        operation = row['NRO_OP']
        bill = row['NRO_FACT_OP']
        dId = counter
        presentValueInvestor = row['VA_PRESENTE_INV']
        if math.isnan(row['MONTO_APLICACION']) == False:
            payedAmount = round(row['MONTO_APLICACION'],2)
        else:
            payedAmount = round(row['VA_PRESENTE_INV'],2)
        billFraction = row['FRAC_FACT_OP'] if row['FRAC_FACT_OP'] else 0

        operations.append({
            'id': id,
            'typeReceipt': typeReceipt,
            'receiptStatus': receiptStatus,
            'date': date,
            'operation': operation,
            'bill': bill,
            'dId': dId,
            'presentValueInvestor': round(presentValueInvestor,2),
            'payedAmount': payedAmount,
            'additionalInterests': round(row['INTESES_ADIC'],2) if row['INTESES_ADIC'] else 0,
            'investorInterest': row['INTERESES_ADIC_INV'] if row['INTERESES_ADIC_INV'] else 0,
            'tableInterest': row['INTERESES_ADIC_MESA'] if row['INTERESES_ADIC_MESA'] else 0,
        })

# print the total of all additional interests
total = 0
for operation in operations:
    if math.isnan(operation['tableInterest']) == False:
        total += operation['tableInterest']


#with open('operation-receipts.json', 'w') as outfile:
#    json.dump(operations, outfile, indent=4)


