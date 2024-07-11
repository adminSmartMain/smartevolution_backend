import pandas as pd
import uuid
import json
# Read the tablas.xlsx file and get the CORREDORES sheet
df = pd.read_excel('ajustes.xlsx', sheet_name='refunds')
# convert all rows to a list of dictionaries
records = df.to_dict('records')

data = []

for row in records:
    data.append({
        "id"         : str(uuid.uuid4()),
        'date'       : str(row['date'])[:10],
        'amount'     : row['amount'],
        'gmAmount'   : row['gmAmount'],
        'beneficiary': row['beneficiary'],
        'accountNumber': row['accountNumber'],
        'observations' : row['observations'],
        'account'    : row['account_id'],
        'client'     : row['client_id'],
        'bank'       : row['bank_id'],
        'applyGM'    : row['applyGM'],
        'rId'        : row['rId'],
    })

# SAVE IN A JSON 
with open('depositsFix.json', 'w') as f:
    json.dump(data, f, indent=4)