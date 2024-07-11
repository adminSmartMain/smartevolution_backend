import pandas as pd
import uuid
import json
# Read the tablas.xlsx file and get the CORREDORES sheet
df = pd.read_excel('tablas.xlsx', sheet_name='CUENTAS CLIENTES - INVERSIONIST')
# convert all rows to a list of dictionaries
accounts = df.to_dict('records')

accountData = []

for account in accounts:
    accountData.append({
        "id": str(uuid.uuid4()),
        "client": account['ID_CLIENTE'],
        "account_number": account['NRO_CUENTA'],
        "primary": False if account['TIPO_CUENTA'] == 'SECUNDARIA' else True,
        "state": True if account['ESTADO_CTA'] == 'ACTIVA' else False,
        'observations': account['OBSERVACIONES'] if account['OBSERVACIONES'] else '',
    })

with open('accounts.json', 'w') as outfile:
    json.dump(accountData, outfile)