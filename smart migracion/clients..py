import pandas as pd
import uuid
import json
# Read the tablas.xlsx file and get the CORREDORES sheet
df = pd.read_excel('newTables.xlsx', sheet_name='CORREDORES')
# convert all rows to a list of dictionaries
brokers = df.to_dict('records')
cities = [
{
    'id': '14f77350-4a75-486b-95fa-8cbe06bf14fc',
    'department':'ac5f98cb-f460-40c3-8de7-e61b0af42466',
    'name': 'bogota'
},
{
    'id': '14f77350-4a75-486b-95fa-8cbe06bf14fc',
    'department':'ac5f98cb-f460-40c3-8de7-e61b0af42466',
    'name': 'bogot a'
},
{
    'id': '14f77350-4a75-486b-95fa-8cbe06bf14fc',
    'department':'ac5f98cb-f460-40c3-8de7-e61b0af42466',
    'name': 'bogot'
},
{
    'id': '14f77350-4a75-486b-95fa-8cbe06bf14fc',
    'department':'ac5f98cb-f460-40c3-8de7-e61b0af42466',
    'name': 'bogotá'
},
{
    'id': '14f77350-4a75-486b-95fa-8cbe06bf14fc',
    'department':'ac5f98cb-f460-40c3-8de7-e61b0af42466',
    'name': 'bogotà'
},
{
    'id': '14f77350-4a75-486b-95fa-8cbe06bf14fc',
    'department':'ac5f98cb-f460-40c3-8de7-e61b0af42466',
    'name': 'bogota dc'
},
{
    'id': '2c6a61fd-d986-4bbb-a9f0-c388732856a4',
    'department':'a186a943-18dd-4dcd-858e-97a6a453b833',
    'name': 'sabaneta'
},
{
    'id': '14f77350-4a75-486b-95fa-8cbe06bf14fc',
    'department':'ac5f98cb-f460-40c3-8de7-e61b0af42466',
    'name': 'bogotá d.c.'
},
{
    'id': '14f77350-4a75-486b-95fa-8cbe06bf14fc',
    'department':'ac5f98cb-f460-40c3-8de7-e61b0af42466',
    'name': 'bogota d.c.'
},
{
    'id': '118dc368-da91-44d0-9b93-2c6e7e94237c',
    'department':'ac5f98cb-f460-40c3-8de7-e61b0af42466',
    'name': 'cota'
},
{
    'id': '791d6a43-1e36-4d98-b026-d563fbef1e59',
    'department':'6fc417d4-806f-4a4f-8c42-ea9ebfe51f45',
    'name': 'ibague'
},
{
    'id': '791d6a43-1e36-4d98-b026-d563fbef1e59',
    'department':'6fc417d4-806f-4a4f-8c42-ea9ebfe51f45',
    'name': 'ibague - tolima'
},
{
    'id': '791d6a43-1e36-4d98-b026-d563fbef1e59',
    'department':'6fc417d4-806f-4a4f-8c42-ea9ebfe51f45',
    'name': 'ibagué'
},
{
    'id': 'e6c40a4b-b894-4838-aa15-d0f7de2360ed',
    'department':'f031bbdb-e1a7-4595-ad89-bd7469ab5e77',
    'name': 'barranquilla'
},
{
    'id': '118dc368-da91-44d0-9b93-2c6e7e94237c',
    'department':'ac5f98cb-f460-40c3-8de7-e61b0af42466',
    'name': 'tocancipa'
},
{
    'id': '118dc368-da91-44d0-9b93-2c6e7e94237c',
    'department':'ac5f98cb-f460-40c3-8de7-e61b0af42466',
    'name': 'tocancipà'
},
{
    'id': 'f2ed392d-6b9b-4519-9d25-fecfc615d204',
    'department':'ac5f98cb-f460-40c3-8de7-e61b0af42466',
    'name': 'bogota - chia'
},
{
    'id': 'f2ed392d-6b9b-4519-9d25-fecfc615d204',
    'department':'ac5f98cb-f460-40c3-8de7-e61b0af42466',
    'name': 'chia'
},
{
    'id': '1ca6ae6c-0a39-4a3c-8bcf-770f3ebd786b',
    'department':'299e96d6-de39-4ca5-9d2a-1ce74b46539f',
    'name': 'pereira'
},
{
    'id': 'a7fda091-5c8f-417b-a27d-ae0d728205ef',
    'department':'8ac029c4-07cc-43cc-9003-46b395287550',
    'name': 'villavicencio'
},
{
    'id': '2c296aec-9359-478d-a71f-5cf607c79bf1',
    'department':'f031bbdb-e1a7-4595-ad89-bd7469ab5e77',
    'name': 'soledad'
},
{
    'id': '12cc4ec1-089e-4c50-b3ea-9354727938d2',
    'department':'a186a943-18dd-4dcd-858e-97a6a453b833',
    'name': 'itagui'
},
{
    'id': 'd1015f99-f167-4f1d-8b95-d0c3cdf3c714',
    'department':'a186a943-18dd-4dcd-858e-97a6a453b833',
    'name': 'medellin'
},
{
    'id': 'd1015f99-f167-4f1d-8b95-d0c3cdf3c714',
    'department':'a186a943-18dd-4dcd-858e-97a6a453b833',
    'name': 'antioquia'
},
{
    'id': '0598199b-570a-44b8-b173-615a9623b3a3',
    'department':'ac5f98cb-f460-40c3-8de7-e61b0af42466',
    'name': 'mosquera'
},
{
    'id': '83a47d9b-c20f-429d-b3cc-edb383527980',
    'department':'035ee8d1-7320-4a4e-a4b9-18c3fe8e04d7',
    'name': 'cali'
},
{
    'id': '83a47d9b-c20f-429d-b3cc-edb383527980',
    'department':'035ee8d1-7320-4a4e-a4b9-18c3fe8e04d7',
    'name': 'cali - valle del cauca'
},
{
    'id': '83a47d9b-c20f-429d-b3cc-edb383527980',
    'department':'035ee8d1-7320-4a4e-a4b9-18c3fe8e04d7',
    'name': 'valle del cauca'
},
{
    'id': '0c493b31-5254-4443-8b2b-2bdb3ca3897a',
    'department':'035ee8d1-7320-4a4e-a4b9-18c3fe8e04d7',
    'name': 'buga'
},
{
    'id': '4f6c3f3c-005d-451e-b5d6-04c74d9fdde4',
    'department':'ac5f98cb-f460-40c3-8de7-e61b0af42466',
    'name': 'tenjo'
},
{
    'id': '4f6c3f3c-005d-451e-b5d6-04c74d9fdde4',
    'department':'ac5f98cb-f460-40c3-8de7-e61b0af42466',
    'name': 'manizales'
},
{
    'id': '7c5c006c-f031-4c3d-b885-33e1cb646008',
    'department':'a186a943-18dd-4dcd-858e-97a6a453b833',
    'name': 'girardota - antioquia'
},
{
    'id': '7c5c006c-f031-4c3d-b885-33e1cb646008',
    'department':'a186a943-18dd-4dcd-858e-97a6a453b833',
    'name': 'girardota - medellin'
},
{
    'id': '7400d4ca-ad17-4cd9-902a-43b2b2e854eb',
    'department':'a186a943-18dd-4dcd-858e-97a6a453b833',
    'name': 'barbosa'
},
{
    'id': 'c940f518-df21-4dfa-8be6-3363b136a241',
    'department':'369d52a1-0d8e-4932-b01a-dc8e9a9efb30',
    'name': 'valledupar'
},
{
    'id': 'c940f518-df21-4dfa-8be6-3363b136a241',
    'department':'369d52a1-0d8e-4932-b01a-dc8e9a9efb30',
    'name': 'velledupar'
},
{
    'id': '5ebda5de-7315-4c25-be3c-26410379c6b1',
    'department':'ac5f98cb-f460-40c3-8de7-e61b0af42466',
    'name': 'soacha'
},
{
    'id': '11c00cbc-61e9-432e-9ec3-e2c6ed457b66',
    'department':'299e96d6-de39-4ca5-9d2a-1ce74b46539f',
    'name': 'dosquebradas'
},
{
    'id': 'bbca9003-5642-4777-b371-981d9f7570ee',
    'department':'ac5f98cb-f460-40c3-8de7-e61b0af42466',
    'name': 'funza - cundinamarca'
},
{
    'id': 'bbca9003-5642-4777-b371-981d9f7570ee',
    'department':'ac5f98cb-f460-40c3-8de7-e61b0af42466',
    'name': 'funza cundinamarca'
},
{
    'id': 'bbca9003-5642-4777-b371-981d9f7570ee',
    'department':'ac5f98cb-f460-40c3-8de7-e61b0af42466',
    'name': 'funza'
},
{
    'id': 'd8daf930-2556-46e2-8493-5dfc1e5a5f86',
    'department':'f49de01a-d649-43c8-9a33-ef29136b46de',
    'name': 'bucaramanga'
},
{
    'id': '17137aa3-7b5e-4119-8036-9dc8e11d9e6b',
    'department':'99a40fb1-328f-441e-97ca-5ab507545649',
    'name': 'neiva'
},
{
    'id': '2ef9b642-8ebd-42d4-af6f-0f899cf62e89',
    'department':'a186a943-18dd-4dcd-858e-97a6a453b833',
    'name': 'envigado'
},
{
    'id': '2ef9b642-8ebd-42d4-af6f-0f899cf62e89',
    'department':'a186a943-18dd-4dcd-858e-97a6a453b833',
    'name': 'envigado - antioquia'
},
{
    'id': '86f28966-ac98-4699-8847-d0a2c5632391',
    'department':'6b1555fa-9e2c-4bbf-a1db-585035803ae7',
    'name': 'PASTO - NARIÑO'
},
{
    'id': '86f28966-ac98-4699-8847-d0a2c5632391',
    'department':'6b1555fa-9e2c-4bbf-a1db-585035803ae7',
    'name': 'pasto - nariño'
},
{
    'id': 'eecf6a75-5a9f-4c19-bc07-53c4d37c3a26',
    'department':'035ee8d1-7320-4a4e-a4b9-18c3fe8e04d7',
    'name': 'yumbo'
},
{
    'id': 'eecf6a75-5a9f-4c19-bc07-53c4d37c3a26',
    'department':'035ee8d1-7320-4a4e-a4b9-18c3fe8e04d7',
    'name': 'yumbo - valle del cauca'
},
{
    'id': 'c4b1d5df-3043-41d0-a25c-146ceac0dd00',
    'department':'035ee8d1-7320-4a4e-a4b9-18c3fe8e04d7',
    'name': 'tulua'
},
{
    'id': '9d2518e0-4008-456e-8b68-82a7b10c2966',
    'department':'5a611246-161a-466e-aee7-0bc82e96a4f9',
    'name': 'santa marta'
},
{
    'id': 'dad6124a-d68a-45b1-b53f-abccb0491d63',
    'department':'035ee8d1-7320-4a4e-a4b9-18c3fe8e04d7',
    'name': 'palmira'
},
{
    'id': 'dad6124a-d68a-45b1-b53f-abccb0491d63',
    'department':'035ee8d1-7320-4a4e-a4b9-18c3fe8e04d7',
    'name': 'palmira valle'
},
{
    'id': '47b7c74e-78e1-4c20-8c90-bf8a7b25946f',
    'department':'a186a943-18dd-4dcd-858e-97a6a453b833',
    'name': 'bello'
},
{
    'id': '47b7c74e-78e1-4c20-8c90-bf8a7b25946f',
    'department':'a186a943-18dd-4dcd-858e-97a6a453b833',
    'name': 'bello antioquia'
},
{
    'id': '1bd92b68-1d8c-445e-bf24-fcaac4d5a9ab',
    'department':'a3fa28b3-6078-480c-bf8c-734e084c148a',
    'name': 'maicao'
},
{
    'id': '1bd92b68-1d8c-445e-bf24-fcaac4d5a9ab',
    'department':'a3fa28b3-6078-480c-bf8c-734e084c148a',
    'name': 'la guajira'
},
{
    'id': '5fc1adfc-0d30-494a-88aa-a93927251d9b',
    'department':'6f8a296a-6b5e-47d7-b0b4-801ef4374f21',
    'name': 'sincelejo'
},
{
    'id': '8a9461e1-614d-49f4-bfaf-3dace24dc3cf',
    'department':'43dc844f-a8dc-469f-af4f-1722907abe9b',
    'name': 'yopal'
},
{
    'id': '22bf605a-4d59-4a8b-95b3-1586fc24fd2d',
    'department':'035ee8d1-7320-4a4e-a4b9-18c3fe8e04d7',
    'name': 'zarzal'
},
{
    'id': '8c69a2ff-deca-40bb-bb31-64d245011489',
    'department':'ac5f98cb-f460-40c3-8de7-e61b0af42466',
    'name': 'girardot'
},
{
    'id': '9337fb5d-634e-4cee-a325-748f426a77f3',
    'department':'8fbaa5a7-76fc-4abf-a623-fa0a107e001b',
    'name': 'cartagena'
},
{
    'id': 'ea2233eb-3bf8-467b-a937-3973668fc637',
    'department':'ac5f98cb-f460-40c3-8de7-e61b0af42466',
    'name': 'gachancipa'
},
]

dataBrokers = [
  {
    "id": "bf3a6757-a2fc-4159-a41e-7a509341e9b3",
    "address": "VARIANTE COTA VIA CHIA KM 1.8 CONJUNTO ARBORADA CASA 50",
    "social_reason": "MAYERLY MEDINA OLAYA",
    "email": "mayo.medina@smartevolution.com.co",
    "phone_number": 3205437158,
    "city": "118dc368-da91-44d0-9b93-2c6e7e94237c",
    "department": "ac5f98cb-f460-40c3-8de7-e61b0af42466",
    "document_number": "65767998",
    "type_identity": "cff883e6-bd88-4cad-9df2-c0e96761f234"
  },
  {
    "id": "0ef18b63-060c-4cc0-a9e2-afe9f6b1e478",
    "address": "COTA",
    "social_reason": "SMART EVOLUTION S.A.S.",
    "email": "andres.ruiz@smartevolution.com.co",
    "phone_number": 3108093225,
    "city": "118dc368-da91-44d0-9b93-2c6e7e94237c",
    "department": "ac5f98cb-f460-40c3-8de7-e61b0af42466",
    "document_number": "901333444",
    "type_identity": "6b1a9326-00c6-4b72-a8b4-4453b889fbb7"
  },
  {
    "id": "893c39c7-e786-4cd2-9901-db85f5d45138",
    "address": "CALLE 182 No. 45-20 APTO 1108 INT 2",
    "social_reason": "JAVIER ORLANDO ORTIZ VASQUEZ",
    "email": "javier_ortiz80@hotmail.com",
    "phone_number": 3008450677,
    "city": "14f77350-4a75-486b-95fa-8cbe06bf14fc",
    "department": "ac5f98cb-f460-40c3-8de7-e61b0af42466",
    "document_number": "14325584",
    "type_identity": "cff883e6-bd88-4cad-9df2-c0e96761f234"
  },
  {
    "id": "64ca6027-6305-4e21-815e-0efadbe3bae5",
    "address": "AK 45 128D 92",
    "social_reason": "MARIA ANDREA ORTIZ PAEZ",
    "email": "mandreaortiz@yahoo.com",
    "phone_number": 3105536869,
    "city": "14f77350-4a75-486b-95fa-8cbe06bf14fc",
    "department": "ac5f98cb-f460-40c3-8de7-e61b0af42466",
    "document_number": "52620380",
    "type_identity": "cff883e6-bd88-4cad-9df2-c0e96761f234"
  },
  {
    "id": "6c333d9c-2984-4bce-a90f-83399b23433d",
    "address": "CL 125 B 57 10 BRR NIZA CORDOBA",
    "social_reason": "CLAUDIA MARIA SIERRA SUAREZ",
    "email": "cmsierra70@yahoo.com",
    "phone_number": 3103210103,
    "city": "14f77350-4a75-486b-95fa-8cbe06bf14fc",
    "department": "ac5f98cb-f460-40c3-8de7-e61b0af42466",
    "document_number": "39785615",
    "type_identity": "cff883e6-bd88-4cad-9df2-c0e96761f234"
  },
  {
    "id": "12d68461-eab7-453e-b990-8955357bebfb",
    "address": "CRA 7 77 07",
    "social_reason": "INTEGRITY HOLDING SAS",
    "email": "mauricio@ibnk.co",
    "phone_number": 3164652545,
    "city": "14f77350-4a75-486b-95fa-8cbe06bf14fc",
    "department": "ac5f98cb-f460-40c3-8de7-e61b0af42466",
    "document_number": "901323336",
    "type_identity": "6b1a9326-00c6-4b72-a8b4-4453b889fbb7"
  },
  {
    "id": "4edf95ad-7e30-47c2-b2d1-6c6ca8ac1d35",
    "address": "CRA 14 N 100-01 T2 AP 301 CONDOMINIO CAMPESTRE LA HACIENDA",
    "social_reason": "ASTRID MILENA SANCHEZ GARCIA",
    "email": "amsanchez.g75@hotmail.com",
    "phone_number": 3105740325,
    "city": "791d6a43-1e36-4d98-b026-d563fbef1e59",
    "department": "6fc417d4-806f-4a4f-8c42-ea9ebfe51f45",
    "document_number": "52228200",
    "type_identity": "cff883e6-bd88-4cad-9df2-c0e96761f234"
  },
  {
    "id": "044be996-7fa2-4add-9528-0c3cb4aff633",
    "address": "Carrera 12 #122-32 apt 310",
    "social_reason": "WILLIAM CARDONA LOPEZ",
    "email": "Williamcardonalopez@gmail.com",
    "phone_number": 3112548017,
    "city": "14f77350-4a75-486b-95fa-8cbe06bf14fc",
    "department": "ac5f98cb-f460-40c3-8de7-e61b0af42466",
    "document_number": "79518685",
    "type_identity": "cff883e6-bd88-4cad-9df2-c0e96761f234"
  },
  {
    "id": "e203cceb-efe7-4112-a048-858cfcb9846b",
    "address": "CRA 26 N 61F 42 AP 302",
    "social_reason": "DANIEL RICARDO LOPEZ RODRIGUEZ",
    "email": "danielricardolopezr@gmail.com",
    "phone_number": 3143410414,
    "city": "14f77350-4a75-486b-95fa-8cbe06bf14fc",
    "department": "ac5f98cb-f460-40c3-8de7-e61b0af42466",
    "document_number": "11259751",
    "type_identity": "cff883e6-bd88-4cad-9df2-c0e96761f234"
  }
]

dataClients              = []
dataLegalRepresentatives = []
dataContacts             = []

# Read the clientes.xlsx file and get the Hoja1 sheet
df = pd.read_excel('newTables.xlsx', sheet_name='CLIENTES')
# convert all rows to a list of dictionaries
clients = df.to_dict('records')
for client in clients:
    clientId = str(uuid.uuid4())
    # check the type of the client
    typeClient = '21cf32d9-522c-43ac-b41c-4dfdf832a7b8' if client['TIPO_CL'] == 'JURIDICO' else '26c885fc-2a53-4199-a6c1-7e4e92032696'
    typeDocument = '6b1a9326-00c6-4b72-a8b4-4453b889fbb7' if client['TIPO_CL'] == 'JURIDICO' else 'cff883e6-bd88-4cad-9df2-c0e96761f234'
    documentNumber = str(client['ID_CL'])
    phone_number = client['TELEFONO_CL']
    if client['TIPO_CL'] == 'JURIDICO':
        social_reason = client['NOMBRE_CL']
        first_name = None
        last_name = None
    else:
        social_reason = None
        # split the names and last names
        names = client['NOMBRE_CL'].split(' ')
        # if the client has two names
        if len(names) == 2:
            first_name = names[0]
            last_name = names[1]
        # if the client has three names
        elif len(names) == 3:
            first_name = names[0] + ' ' + names[1]
            last_name = names[2]
        # if the client has more than three names
        else:
            first_name = names[0] + ' ' + names[1]
            last_name = names[2] + ' ' + names[3]

    birth_date  = str(client['FECHA_NAC_CL'])
    citizenship = '9729f179-298e-4616-8aa4-3ce44dd18449' if client['CIUDAD_CL'] != 'JALISCO' else 'eb835437-5512-415f-93fb-eeecf793132d'
    address     = client['DIRECCION_CL']
    email       = client['EMAIL_CL']
    created_at  = str(client['FECHA_INCLUSION'])
    # broker 
    searchBroker = [broker for broker in dataBrokers if broker['document_number'] == str(client['ID_CORR'])]
    if client['ID_CORR'] == 0:
        broker = None
    else:
        if searchBroker:
            broker = searchBroker[0]['id']
        else:
            broker = None
    user = None
    entered_by = '9eef1a12-5f95-4228-a21e-11287bb0cd95'
    ciiu = client['N_ACTIVIDAD_CIIU']

    if client['CIUDAD_CL'] != 'JALISCO':
        cityFilter = [city for city in cities if city['name'] == client['CIUDAD_CL'].lower()]
        # check if the city exists
        dataCity   = cityFilter[0] if cityFilter else None
        city       = dataCity['id'] 
        # check if the city exists
        department = dataCity['department']
    else:
        city = None
        department = None
    
    dataClients.append({
        'id': clientId,
        'type_client': typeClient,
        'type_identity': typeDocument,
        'document_number': documentNumber,
        'social_reason': social_reason,
        'first_name': first_name,
        'last_name': last_name,
        'birth_date': birth_date,
        'citizenship': citizenship,
        'address': address,
        'email': email,
        'phone_number': phone_number,
        'created_at': created_at,
        'broker': broker,
        'user': user,
        'entered_by': entered_by,
        'ciiu': ciiu,
        'city': city,
        'department': department
    })

    # get legal representative data
    if type(client['NOMBRE_RPL']) != float:
        rlType_identity =  'cff883e6-bd88-4cad-9df2-c0e96761f234'
        rlClient = clientId
        rlDocument_number = str(client['ID_RPL'])
        rlFullName = client['NOMBRE_RPL'].split(' ')
        # if the client has two names
        if len(rlFullName) == 2:
            rlFirstName = rlFullName[0]
            rlLastName = rlFullName[1]
        elif len(rlFullName) == 1:
                contactFirstName = contactFullName[0] if contactFullName[0] != '' else None
                contactLastName = None
        # if the client has three names
        elif len(rlFullName) == 3:
            rlFirstName = rlFullName[0]
            rlLastName = rlFullName[1] + ' ' + rlFullName[2]
        # if the client has more than three names
        elif len(rlFullName) == 5:
            rlFirstName = rlFullName[0] + ' ' + rlFullName[1]
            rlLastName = rlFullName[2] + ' ' + rlFullName[3] + ' ' + rlFullName[4]
        else:
            rlFirstName = rlFullName[0] + ' ' + rlFullName[1]
            rlLastName = rlFullName[2] + ' ' + rlFullName[3]
        rlBirth_date = str(client['FECHA_NAC_RPL'])
        rlAddress = client['DIRECCION_RPL']
        if type(client['CIUDAD_RPL']) == float:
            rlCity = None
            rlDepartment = None
        else:
            rlCityFilter = [city for city in cities if city['name'] == client['CIUDAD_RPL'].lower()]
            # check if the city exists
            rlDataCity   = rlCityFilter[0] if rlCityFilter else None
            rlCity       = rlDataCity['id'] 
            # check if the city exists
            rlDepartment = rlDataCity['department']
        rlCitizenship = '9729f179-298e-4616-8aa4-3ce44dd18449'
        rlPhone_number = client['TELEFONO_RPL']
        rplEmail       = client['EMAIL_RPL']
        rlPosition     = client['CARGO_RPL']

        
        dataLegalRepresentatives.append({
            'id': str(uuid.uuid4()),
            'type_identity': rlType_identity,
            'client': rlClient,
            'document_number': rlDocument_number,
            'first_name': rlFirstName,
            'last_name': rlLastName,
            'social_reason':None,
            'birth_date': rlBirth_date,
            'address': rlAddress,
            'city': rlCity,
            'department': rlDepartment,
            'citizenship': rlCitizenship,
            'phone_number': rlPhone_number,
            'email': rplEmail,
            'position': rlPosition
        })

        if type(client['NOMBRE_CONTACTO1']) == float or type(client['NOMBRE_CONTACTO1']) == int:
            pass
        else:
            contactFullName = client['NOMBRE_CONTACTO1'].split(' ')
            # if the client has two names
            if len(contactFullName) == 2:
                contactFirstName = contactFullName[0]
                contactLastName = contactFullName[1]
            elif len(contactFullName) == 1:
                contactFirstName = contactFullName[0] if contactFullName[0] != '' else None
                contactLastName = None
            # if the client has three names
            elif len(contactFullName) == 3:
                contactFirstName = contactFullName[0]
                contactLastName = contactFullName[1] + ' ' + contactFullName[2]
            # if the client has more than three names
            elif len(contactFullName) == 5:
                contactFirstName = contactFullName[0] + ' ' + contactFullName[1]
                contactLastName = contactFullName[2] + ' ' + contactFullName[3] + ' ' + contactFullName[4]
            else:
                contactFirstName = contactFullName[0] + ' ' + contactFullName[1]
                contactLastName = contactFullName[2] + ' ' + contactFullName[3]
            dataContacts.append({
                'id': str(uuid.uuid4()),
                'client': clientId,
                'first_name': contactFirstName,
                'last_name': contactLastName,
                'social_reason': None,
                'phone_number': client['TELEFONO_CONTACTO1'],
                'email': client['EMAIL_CONTACTO1'],
                'position': client['CARGO_CONTACTO1']
            })
        
        if type(client['NOMBRE_CONTACTO2']) == float or type(client['NOMBRE_CONTACTO2']) == int:
            pass
        else:
            contactFullName = client['NOMBRE_CONTACTO2'].split(' ')
            # if the client has two names
            if len(contactFullName) == 2:
                contactFirstName = contactFullName[0]
                contactLastName = contactFullName[1]
            # if the client has three names
            elif len(contactFullName) == 3:
                contactFirstName = contactFullName[0]
                contactLastName = contactFullName[1] + ' ' + contactFullName[2]
            # if the client has more than three names
            elif len(contactFullName) == 5:
                contactFirstName = contactFullName[0] + ' ' + contactFullName[1]
                contactLastName = contactFullName[2] + ' ' + contactFullName[3] + ' ' + contactFullName[4]
            elif len(contactFullName) == 1:
                contactFirstName = contactFullName[0] if contactFullName[0] != '' else None
                contactLastName = None
            else:
                contactFirstName = contactFullName[0] + ' ' + contactFullName[1]
                contactLastName = contactFullName[2] + ' ' + contactFullName[3]
            dataContacts.append({
                'id': str(uuid.uuid4()),
                'client': clientId,
                'first_name': contactFirstName,
                'last_name': contactLastName,
                'social_reason': None,
                'phone_number': client['TELEFONO_CONTACTO2'],
                'email': client['EMAIL_CONTACTO2'],
                'position': client['CARGO_CONTACTO2']
            })



# create a json file for each data
with open('dataClients.json', 'w') as outfile:
    json.dump(dataClients, outfile)

with open('dataLegalRepresentatives.json', 'w') as outfile:
    json.dump(dataLegalRepresentatives, outfile)

with open('dataContacts.json', 'w') as outfile:
    json.dump(dataContacts, outfile)

with open('dataBrokers.json', 'w') as outfile:
    json.dump(dataBrokers, outfile)
    



