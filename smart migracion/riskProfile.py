import pandas as pd
import uuid
import json
# Read the tablas.xlsx file and get the CORREDORES sheet
df = pd.read_excel('tablas.xlsx', sheet_name='PERFIL DE RIESGOS')
# convert all rows to a list of dictionaries
accounts = df.to_dict('records')

dataRiskProfile = []

banks = [
    {'name':'BANCOLOMBIA', 'id':'19be658a-dbc1-487a-b42f-11b561f4f781'},
    {'name':'BANCO DE BOGOTÁ', 'id':'135e5406-0c3e-419a-9bcc-d89d32c91003'},
    {'name':'BANCO DAVIVIENDA', 'id':'5924d405-f89a-4b68-ade3-c25e71d985b8'},
    {'name':'BANCO ITAÚ CORPBANCA COLOMBIA S.A.', 'id':'89b6a6a0-4cfc-4984-a450-acb589c8f211'},
    {'name':'BANCO SCOTIABANK COLPATRIA', 'id':'97610e09-7102-4161-9fed-58ca88b6007a'},
    {'name':'BANCO AV VILLAS', 'id':'35b3a881-1472-4d67-bf2a-808acaee1e89'},
    {'name':'BANCO GNB SUDAMERIS', 'id':'6166932d-9edd-48b9-aa06-425cb6eb100e'},
    {'name':'BANCO CAJA SOCIAL', 'id':'310c13b3-7183-47b5-b720-66d879ba688f'},
    {'name':'BANCO BBVA', 'id':'af950f99-a98c-4ef4-8905-e9e47d014ecb'}
]

for account in accounts:
    id = str(uuid.uuid4())
    client = account['ID_CL']
    gmf=True if account['APLICA_GMF']     == -1 else False
    iva=True if account['APLICA_ICA']     == -1 else False
    ica=True if account['APLICA_RET_IVA'] == -1 else False
    discount_rate=account['TASA_DESC_EMISOR'] * 100
    discount_rate_investor=account['TASA_INVERSIONISTA'] * 100
    emitter_balance=account['CUPO_EMISOR']
    investor_balance=account['CUPO_INVERSIONISTA']
    payer_balance=account['CUPO_PAGADOR']
    if type(account['NRO_CUENTA']) == float:
        account_number = None
    else:
        account_number = account['NRO_CUENTA']
    if type(account['TIPO_CUENTA']) == float:
        account_type = None
    else:
        account_type='9a58138a-479c-4157-9208-b6c7c27c8752' if account['TIPO_CUENTA'] == 'AHORRO' else '3d0b1bd6-85fb-47af-b89b-329a6a24126b'
    if type(account['NOMBRE_BANCO']) == float:
        bank = None
    else:
        searchBank = list(filter(lambda b: b['name'] == account['NOMBRE_BANCO'], banks))
        bank = searchBank[0]['id'] if len(searchBank) > 0 else None
    dataRiskProfile.append({
        'id': id,
        'client': client,
        'gmf': gmf,
        'iva': iva,
        'ica': ica,
        'discount_rate': discount_rate,
        'discount_rate_investor': discount_rate_investor,
        'investor_balance': investor_balance,
        'emitter_balance': emitter_balance,
        'payer_balance': payer_balance,
        'bank': bank,
        'account_type': account_type,
        'account_number': account_number,
        'name':account['NOMBRE_CL']
    })

with open('dataRiskProfile.json', 'w') as outfile:
    json.dump(dataRiskProfile, outfile)
