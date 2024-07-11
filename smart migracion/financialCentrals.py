import pandas as pd
import uuid
import json
from datetime import datetime
# Read the tablas.xlsx file and get the CORREDORES sheet
df = pd.read_excel('newTables.xlsx', sheet_name='PERFIL FINANCIERO')
# convert all rows to a list of dictionaries
data = df.to_dict('records')
analysis = []
centrals = []
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
    {'name':'BANCO AGRARIO DE COLOMBIA', 'id':'b54d79aa-d4c7-41fb-992c-fc5ee8aff487'},
    {
		"id" : "0554a011-17b1-4d69-b019-2eb4ab1a96fe",
		"state" : 1,
		"created_at" : "2023-07-04 14:15:52.433985",
		"updated_at" : None,
		"name" : "FINANPRIMAS",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "12ee7294-ff73-430e-8cee-dd8e94cc0412",
		"state" : 1,
		"created_at" : "2023-07-04 14:13:14.241013",
		"updated_at" : None,
		"name" : "Banco Pichincha",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "135e5406-0c3e-419a-9bcc-d89d32c91003",
		"state" : 1,
		"created_at" : "2023-07-04 14:13:13.029329",
		"updated_at" : None,
		"name" : "Banco de Bogotá",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "149651a3-d627-45b2-95c1-bec2323e60d5",
		"state" : 1,
		"created_at" : "2023-07-04 14:15:51.483518",
		"updated_at" : None,
		"name" : "Small Business",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "19be658a-dbc1-487a-b42f-11b561f4f781",
		"state" : 1,
		"created_at" : "2023-07-04 14:13:12.943600",
		"updated_at" : None,
		"name" : "Bancolombia",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "1c063292-dcde-4788-9320-476ad33322e4",
		"state" : 1,
		"created_at" : "2023-07-04 14:13:13.980655",
		"updated_at" : None,
		"name" : "Banco Union",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "23f52fc1-a63d-4f7a-b930-3883a9985c01",
		"state" : 1,
		"created_at" : "2023-07-04 14:15:52.865724",
		"updated_at" : None,
		"name" : "CLARO",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "2cb0ded1-4077-4f7f-9681-5ef6418f9db5",
		"state" : 1,
		"created_at" : "2023-07-04 14:15:53.214945",
		"updated_at" : None,
		"name" : "FINAGRO",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "310c13b3-7183-47b5-b720-66d879ba688f",
		"state" : 1,
		"created_at" : "2023-07-04 14:13:13.808907",
		"updated_at" : None,
		"name" : "Banco Caja Social",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "317ddf91-422b-46cc-9d7a-506b80b610b7",
		"state" : 1,
		"created_at" : "2023-07-04 14:13:14.411198",
		"updated_at" : None,
		"name" : "Banco Finandina",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "32b83850-5832-4fa9-83ac-ba7ceea6e597",
		"state" : 1,
		"created_at" : "2023-07-04 14:15:51.824470",
		"updated_at" : None,
		"name" : "ND",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "35b3a881-1472-4d67-bf2a-808acaee1e89",
		"state" : 1,
		"created_at" : "2023-07-04 14:13:13.893886",
		"updated_at" : None,
		"name" : "Banco AV Villas",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "3932db95-5ed5-4740-be7d-6e62d6bc38c5",
		"state" : 1,
		"created_at" : "2023-07-04 14:15:51.391726",
		"updated_at" : None,
		"name" : "No Registra",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "3f197066-77cd-4185-b41f-0ea45ccaed11",
		"state" : 1,
		"created_at" : "2023-07-04 14:15:51.291621",
		"updated_at" : None,
		"name" : "Banco Serfinanza",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "42b4f672-5bf3-4376-bcf3-8ca2e4cc01f5",
		"state" : 1,
		"created_at" : "2023-07-04 14:15:52.259694",
		"updated_at" : None,
		"name" : "Comercializadora Santander",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "5924d405-f89a-4b68-ade3-c25e71d985b8",
		"state" : 1,
		"created_at" : "2023-07-04 14:13:13.199519",
		"updated_at" : None,
		"name" : "Davivienda",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "6166932d-9edd-48b9-aa06-425cb6eb100e",
		"state" : 1,
		"created_at" : "2023-07-04 14:13:13.637638",
		"updated_at" : None,
		"name" : "GNB Sudameris",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "655a30f7-edc8-43f9-a1c0-50e2eae5a63a",
		"state" : 1,
		"created_at" : "2023-07-04 14:13:14.326072",
		"updated_at" : None,
		"name" : "Banco W",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "6afa9bbf-d917-4976-b91a-22d6107b944a",
		"state" : 1,
		"created_at" : "2023-07-04 14:15:53.301292",
		"updated_at" : None,
		"name" : "Coltefinanciera",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "70dea415-25cc-442b-9a01-42ddcd0a1591",
		"state" : 1,
		"created_at" : "2023-07-04 14:15:51.739583",
		"updated_at" : None,
		"name" : "Servientrega",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "711685f8-11a4-400c-96e6-e70c70b1d2e8",
		"state" : 1,
		"created_at" : "2023-07-04 14:13:13.371363",
		"updated_at" : None,
		"name" : "Banco Popular",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "7608290a-f1f0-4c57-afb7-21b82e19aca0",
		"state" : 1,
		"created_at" : "2023-07-04 14:15:52.348863",
		"updated_at" : None,
		"name" : "TDH",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "7dbcd53f-049c-40d1-8f35-692535839c8f",
		"state" : 1,
		"created_at" : "2023-07-04 14:15:51.569088",
		"updated_at" : None,
		"name" : "ol",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "7ef3b22a-0695-44c2-97dd-df964f749eb0",
		"state" : 1,
		"created_at" : "2023-07-04 14:15:52.606965",
		"updated_at" : None,
		"name" : "Finanzauto",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "7f4676c0-6b67-4ec6-8f27-1cd66576ed63",
		"state" : 1,
		"created_at" : "2023-07-04 14:13:14.156079",
		"updated_at" : None,
		"name" : "Banco Falabella",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "817f4e91-70c6-490a-9599-81ee1c75dd29",
		"state" : 1,
		"created_at" : "2023-07-04 14:15:51.996471",
		"updated_at" : None,
		"name" : "Iris Bank",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "85507ced-3a2f-471c-92d7-aad3ed707a55",
		"state" : 1,
		"created_at" : "2023-07-04 14:15:51.654417",
		"updated_at" : None,
		"name" : "Geomatrix",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "89b6a6a0-4cfc-4984-a450-acb589c8f211",
		"state" : 1,
		"created_at" : "2023-07-04 14:13:13.548167",
		"updated_at" : None,
		"name" : "Banco itaú",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "97610e09-7102-4161-9fed-58ca88b6007a",
		"state" : 1,
		"created_at" : "2023-07-04 14:13:13.458631",
		"updated_at" : None,
		"name" : "Scotiabank Colpatria",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "9a5ed5a9-0607-4f7b-886c-2a72bd153f87",
		"state" : 1,
		"created_at" : "2023-07-04 14:13:13.114644",
		"updated_at" : None,
		"name" : "Banco de Occidente",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "a0c704e6-84d7-4649-b4ae-58715ddca1ba",
		"state" : 1,
		"created_at" : "2023-07-04 14:13:14.752488",
		"updated_at" : None,
		"name" : "Bancoldex",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "a49209c9-9280-4c93-a4f1-80b9e2fb8aa8",
		"state" : 1,
		"created_at" : "2023-07-04 14:13:14.070914",
		"updated_at" : None,
		"name" : "Bancoomeva",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "a747178f-368e-4989-b3e6-d19f10d658a2",
		"state" : 1,
		"created_at" : "2023-07-04 14:15:53.129220",
		"updated_at" : None,
		"name" : "Giros y Finanzas",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "a9a8f173-9308-4338-9d06-8294014fd434",
		"state" : 1,
		"created_at" : "2023-07-04 14:13:14.496316",
		"updated_at" : None,
		"name" : "Bancamía",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "aea432c1-8698-47f1-a900-d39c743a6ac7",
		"state" : 1,
		"created_at" : "2023-07-04 14:15:52.081842",
		"updated_at" : None,
		"name" : "Laumayer",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "af31995b-4454-43de-a6f2-249ebad4c3a9",
		"state" : 1,
		"created_at" : "2023-07-04 14:15:52.778771",
		"updated_at" : None,
		"name" : "NEXSYS",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "af950f99-a98c-4ef4-8905-e9e47d014ecb",
		"state" : 1,
		"created_at" : "2023-07-04 14:13:13.286267",
		"updated_at" : None,
		"name" : "BBVA",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "b54d79aa-d4c7-41fb-992c-fc5ee8aff487",
		"state" : 1,
		"created_at" : "2023-07-04 14:13:13.723578",
		"updated_at" : None,
		"name" : "Banco Agrario",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "b7f28051-6061-487b-80ee-11422694cea4",
		"state" : 1,
		"created_at" : "2023-07-04 14:15:52.957372",
		"updated_at" : None,
		"name" : "Otros",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "bce5a238-6f43-4ee7-ba57-1b42607cf172",
		"state" : 1,
		"created_at" : "2023-07-04 14:15:52.519961",
		"updated_at" : None,
		"name" : "Team Foods",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "be57c937-4069-46c6-a558-69b46279e965",
		"state" : 1,
		"created_at" : "2023-07-04 14:15:52.692916",
		"updated_at" : None,
		"name" : "sempli",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "cae8c7e3-2ef1-429b-a4c0-2fec5531bf8c",
		"state" : 1,
		"created_at" : "2023-07-04 14:13:14.667411",
		"updated_at" : None,
		"name" : "Banco Cooperativo CoopCentral",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "d1a9cf02-5fea-49e4-a553-d1b59aa6f91f",
		"state" : 1,
		"created_at" : "2023-07-04 14:15:53.042838",
		"updated_at" : None,
		"name" : "Granaliados",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "d6797dff-494f-4a1f-b515-f1d91025f68e",
		"state" : 1,
		"created_at" : "2023-07-04 14:15:52.170477",
		"updated_at" : None,
		"name" : "Corporacion Interactuar",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "e241f2cb-5d0d-40a0-a13b-925031adf5f2",
		"state" : 1,
		"created_at" : "2023-07-04 14:15:51.909980",
		"updated_at" : None,
		"name" : "No registra endeudamiento con el sector financiero",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	},
	{
		"id" : "fb43789b-2aff-4e79-b53d-65ac95ba5d5e",
		"state" : 1,
		"created_at" : "2023-07-04 14:13:14.581796",
		"updated_at" : None,
		"name" : "Banco Credifinanciera",
		"user_created_at_id" : None,
		"user_updated_at_id" : None
	}
]



for row in data:
    clientId   = row['ID_CL']
    clientName = row['NOMBRE_CL']
    analysis.append({
        'id'         : str(uuid.uuid4()),
        'clientId'   : clientId,
        'clientName' : clientName,
        'financial'  :row['ANALISIS_FINANC']  if row['ANALISIS_FINANC'] else '',
        'qualitative': row['RES_CUALITATIVO'] if row['RES_CUALITATIVO'] else '',
    })
    # get the bank id from the name
    if type(row['ENTIDAD1'] != float):
        searchBank = list(filter(lambda b: b['name'] == row['ENTIDAD1'], banks))
        bank1        = searchBank[0]['id'] if len(searchBank) > 0 else None
        calification1 = row['CALIFICACION1']
        value1        = row['SALDO_CTRAL1']
    else:
        bank1 = None
        calification1 = None
        value1 = None
    
    # get the bank id from the name
    if type(row['ENTIDAD2'] != float):
        searchBank = list(filter(lambda b: b['name'] == row['ENTIDAD2'], banks))
        bank2        = searchBank[0]['id'] if len(searchBank) > 0 else None
        calification2 = row['CALIFICACION2']
        value2        = row['SALDO_CTRAL2']
    else:
        bank2         = None
        calification2 = None
        value2        = None
    
    # get the bank id from the name
    if type(row['ENTIDAD3'] != float):
        searchBank = list(filter(lambda b: b['name'] == row['ENTIDAD3'], banks))
        bank3       = searchBank[0]['id'] if len(searchBank) > 0 else None
        calification3 = row['CALIFICACION3']
        value3        = row['SALDO_CTRAL3']
    else:
        bank3        = None
        calification3 = None
        value3        = None
    
    # get the bank id from the name
    if type(row['ENTIDAD4'] != float):
        searchBank = list(filter(lambda b: b['name'] == row['ENTIDAD4'], banks))
        bank4        = searchBank[0]['id'] if len(searchBank) > 0 else None
        calification4 = row['CALIFICACION4']
        value4        = row['SALDO_CTRAL4']
    else:
        bank4        = None
        calification4 = None
        value4        = None
    
    # get the bank id from the name
    if type(row['ENTIDAD5'] != float):
        searchBank = list(filter(lambda b: b['name'] == row['ENTIDAD5'], banks))
        bank5        = searchBank[0]['id'] if len(searchBank) > 0 else None
        calification5 = row['CALIFICACION5']
        value5        = row['SALDO_CTRAL5']
    else:
        bank5         = None
        calification5 = None
        value5        = None
    
    # append all the data
    centrals.append({
        'id'           : str(uuid.uuid4()),
        'clientId'     : clientId,
        'clientName'   : clientName,
        'bank'        : bank1,
        'rating': calification1,
        'centralBalances'       : value1,
    })
    centrals.append({
        'id'           : str(uuid.uuid4()),
        'clientId'     : clientId,
        'clientName'   : clientName,
        'bank'        : bank2,
        'rating': calification2,
        'centralBalances'       : value2,
    })
    centrals.append({
        'id'           : str(uuid.uuid4()),
        'clientId'     : clientId,
        'clientName'   : clientName,
        'bank'        : bank3,
        'rating': calification3,
        'centralBalances'       : value3,
    })
    centrals.append({
        'id'           : str(uuid.uuid4()),
        'clientId'     : clientId,
        'clientName'   : clientName,
        'rating': calification4,
        'bank'        : bank4,
        'centralBalances'       : value4,
    })
    centrals.append({
        'id'           : str(uuid.uuid4()),
        'clientId'     : clientId,
        'clientName'   : clientName,
        'bank'        : bank5,
        'rating': calification5,
        'centralBalances'       : value5,
    })

# save the data to a json
with open('financialCentrals.json', 'w') as outfile:
    json.dump(centrals, outfile)
