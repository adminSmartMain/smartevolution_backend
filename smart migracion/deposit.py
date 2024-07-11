import pandas as pd
import uuid
import json
from datetime import datetime
# Read the tablas.xlsx file and get the CORREDORES sheet
df = pd.read_excel('newTables.xlsx', sheet_name='GIROS INVERSIONISTAS')
# convert all rows to a list of dictionaries
data = df.to_dict('records')

deposits = []
for row in data:
    id           = str(uuid.uuid4())
    dId          = row['NRO_OP']
    date         = str(row['FECHA_RAD_OP'])
    # delete the  00:00:00 from the str
    date         = date[:10]
    client       = row['ID_INVERSIONISTA_OP']
    account      = row['CUENTA_INVERSIONISTA_OP_GIRO']
    amount       = row['VA_PRESENTE_INV']
    description  = row['OBSERVACIONES']

    deposits.append({
        'id': id,
        'dId': dId,
        'date': date,
        'client': client,
        'account': account,
        'amount': amount,
        'description': description
    })


# save the data in a json file
with open('deposits.json', 'w') as f:
    json.dump(deposits, f, indent=4)


