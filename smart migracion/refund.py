import pandas as pd
import uuid
import json
from datetime import datetime
# Read the tablas.xlsx file and get the CORREDORES sheet
df = pd.read_excel('newTables.xlsx', sheet_name='REINTEGROS INVERSIONISTAS')
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

refunds = []

for row in data:
    id   = str(uuid.uuid4())
    rId  = row['NRO_OP']
    date = str(row['FECHA_RAD_OP'])
    # delete the  00:00:00 from the str
    date = date[:10]
    client = row['ID_INVERSIONISTA_OP']
    account = row['CUENTA_INVERSIONISTA_OP_REINTEGRO']
    amount  = row['VA_PRESENTE_INV'] * -1
    applyGM = True if row['GMF_OP'] == -1 else False
    gmAmount = row['MONTO_GMF']
    beneficiary = row['BENEFICIARIO']
    bank = row['BANCO']
    accountType = row['TIPO_CUENTA']
    accountNumber = row['NRO_CUENTA']
    observations = row['OBSERVACIONES']

    # get the bank 
    for b in banks:
        if b['name'] == bank:
            bank = b['id']
            break


    if accountType == 'AHORRO' or accountType == 'CORRIENTE':
        accountType = '9a58138a-479c-4157-9208-b6c7c27c8752' if row['TIPO_CUENTA'] == 'AHORRO' else '3d0b1bd6-85fb-47af-b89b-329a6a24126b'
    else:
        accountType = None
    
    refunds.append({
        'id': id,
        'rId': rId,
        'date': date,
        'client': client,
        'account': account,
        'amount': amount,
        'applyGM': applyGM,
        'gmAmount': gmAmount,
        'beneficiary': beneficiary,
        'bank': bank,
        'accountType': accountType,
        'accountNumber': accountNumber,
        'observations': observations
    })

# save the data in a json file
with open('refunds.json', 'w') as f:
    json.dump(refunds, f, indent=4)
    
