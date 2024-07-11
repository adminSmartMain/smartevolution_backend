import pandas as pd
import uuid
import json
from datetime import datetime
# Read the tablas.xlsx file and get the CORREDORES sheet
df = pd.read_excel('newTables.xlsx', sheet_name='DESCUENTOS RESUMEN NEGOCIACION')
# convert all rows to a list of dictionaries
data = df.to_dict('records')

dataNS = []

accountingControls = [
    {
        'id':"0799fc62-fd65-4bef-af56-6747fbcadac4",
        'name':'COMPENSACIÓN'
    },
    {
        'id':"39e0b709-cff5-42e2-b729-6a1e0a09ae07",
        'name':'OTRO'
    },
{       'id':"5d6524f0-521b-43b2-bf85-ea4c02e2a901",
        'name':'RECOMPRA'
    },
    
]


accounts = [
    {'name':'PARTICULARES', 'id':'e12e227a-aa84-405b-be7f-60060e90bf52'},
    {'name':'DE',  'id':'3cfdc215-060d-468e-9b6f-ac16d4086584'},
    {'name':'CAJA', 'id':'6e3b9251-33bc-460c-8c94-59c8eb473923'}
    ]

for row in data:
    id            = str(uuid.uuid4())
    opId          = row['NRO_OP_ASOC']
    description   = row['DESCRIPCION_DESC']
    amount        = row['MONTO_DESC']
    date          = str(row['FECHA_DESC'])[:10]
    third         = row['ID_CLIENTE_DESC']
    # search the accounting control if contains the description
    for control in accountingControls:
        try:
            if control['name'] in row['TIPO_DESC']:
                typeExpenditure = control['id']
                break
        except:
            typeExpenditure = None
    # search the account if contains the description
    for accountx in accounts:
        try:
            if accountx['name'] in row['DCC_DESC']:
                account = accountx['id']
                break
        except:
            account = None

    dataNS.append({
        'id': id,
        'opId': opId,
        'description': description,
        'amount': amount,
        'date': date,
        'third': third,
        'typeExpenditure': typeExpenditure,
        'account': account
    })

# save into a json
with open('negotiationSummaryData.json', 'w') as file:
    json.dump(dataNS, file, indent=4)

    