import pandas as pd
import uuid
import json
from datetime import datetime
# Read the tablas.xlsx file and get the CORREDORES sheet
df = pd.read_excel('newTables.xlsx', sheet_name='GIROS EMISOR')
# convert all rows to a list of dictionaries
data = df.to_dict('records')

banks = [
    {'name':'BANCOLOMBIA', 'id':'19be658a-dbc1-487a-b42f-11b561f4f781'},
    {'name':'BANCO DE BOGOTÁ', 'id':'135e5406-0c3e-419a-9bcc-d89d32c91003'},
    {'name':'BANCO DAVIVIENDA', 'id':'5924d405-f89a-4b68-ade3-c25e71d985b8'},
    {'name':'BANCO ITAÚ CORPBANCA COLOMBIA S.A.', 'id':'89b6a6a0-4cfc-4984-a450-acb589c8f211'},
    {'name':'BANCO SCOTIABANK COLPATRIA', 'id':'97610e09-7102-4161-9fed-58ca88b6007a'},
    {'name':'BANCO SCOTIABANK COLPATRIA ', 'id':'97610e09-7102-4161-9fed-58ca88b6007a'},
    {'name':'BANCO AV VILLAS', 'id':'35b3a881-1472-4d67-bf2a-808acaee1e89'},
    {'name':'BANCO AV VILLAS ', 'id':'35b3a881-1472-4d67-bf2a-808acaee1e89'},
    {'name':'BANCO GNB SUDAMERIS', 'id':'6166932d-9edd-48b9-aa06-425cb6eb100e'},
    {'name':'BANCO CAJA SOCIAL', 'id':'310c13b3-7183-47b5-b720-66d879ba688f'},
    {'name':'BANCO BBVA', 'id':'af950f99-a98c-4ef4-8905-e9e47d014ecb'},
    {'name':'BANCO DE OCCIDENTE', 'id':'9a5ed5a9-0607-4f7b-886c-2a72bd153f87'},
    {'name':'BANCO POPULAR', 'id':'711685f8-11a4-400c-96e6-e70c70b1d2e8'},
    {'name':'BANCO CAJA SOCIAL ', 'id':'310c13b3-7183-47b5-b720-66d879ba688f'},
    {'name':'BANCO PICHINCHA', 'id':'12ee7294-ff73-430e-8cee-dd8e94cc0412'},
    {'name':'BANCO AGRARIO DE COLOMBIA', 'id':'b54d79aa-d4c7-41fb-992c-fc5ee8aff487'}
]

accounts = [
    {'name':'Bancolombia Cta Cte', 'id':'b319487a-cbf8-440a-a7ed-ab0f83c174be'},
    {'name':'BBVA Cta Cte', 'id':'c8ed80c0-d761-4010-954c-baf38bf02337'}
    ]

emitterDeposits    = []
accountingControls = []

for row in data:
    id            = str(uuid.uuid4()) 
    date          = str(row['FECHA_GIRO_E'])
    # delete the  00:00:00 from the str
    date          = date[:10]
    client        = row['ID_CLIENTE_GIRO_E']
    clientName    = row['NOMBRE_CLIENTE_GIRO_E']
    operation     = row['NRO_OP_ASOC_E']
    amount        = row['MONTO_GIRO_E']
    bank          = row['BANCO_GIRO']
    beneficiary   = row['BENEFICIARIO_GIRO_E']
    accountType   = '9a58138a-479c-4157-9208-b6c7c27c8752' if row['TIPO_CUENTA_GIRO'] == 'AHORRO' else '3d0b1bd6-85fb-47af-b89b-329a6a24126b'
    accountNumber = row['NRO_CUENTA_GIRO']
    edId          = row['NRO_OP_GIRO_E']

    # get the bank id
    bankId = ''
    for b in banks:
        if b['name'] == bank:
            bankId = b['id']
            break
    bank = bankId

    if row['TIPO_EGRESO_GIRO_E'] == 'TRANSFERENCIA':
        id = str(uuid.uuid4())
        type = 'f6d29b11-ecfe-417e-887f-75ddc43b0017'
        # get the account id
        accountId = ''
        for a in accounts:
            # if row['CC_GIRO_E'] contains bancolombia the account is Bancolombia Cta Cte else is BBVA Cta Cte
            if 'Bancolombia' in row['CC_GIRO_E']:
                if a['name'] == 'Bancolombia Cta Cte':
                    accountId = a['id']
                    break
            elif 'BBVA' in row['CC_GIRO_E']:
                if a['name'] == 'BBVA Cta Cte':
                    accountId = a['id']
                    break
        account = accountId
        observations = ""
        accountingControls.append({
            'id': id,
            'type': type,
            'account': account,
            'observations': observations,
            'emitterDeposit': edId
        })
    emitterDeposits.append({
        'id': id,
        'date': date,
        'client': client,
        'clientName': clientName,
        'operation': operation,
        'amount': amount,
        'bank': bank,
        'beneficiary': beneficiary,
        'accountType': accountType,
        'accountNumber': accountNumber,
        'edId': edId
    })


# create the json objects 
with open('emitterDeposits.json', 'w') as outfile:
    json.dump(emitterDeposits, outfile)

with open('accountingControls.json', 'w') as outfile:
    json.dump(accountingControls, outfile)