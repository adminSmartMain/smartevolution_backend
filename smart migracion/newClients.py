import pandas as pd
import uuid
import json
# Read the tablas.xlsx file and get the CORREDORES sheet
df = pd.read_excel('july23.xlsx', sheet_name='clients')
# convert all rows to a list of dictionaries
clients = df.to_dict('records')

data = []
for row in clients:
    data.append({
        'document_number': row['document_number'],
        'social_reason': row['social_reason'],
        'address': row['address'],
        'email': row['email'],
        'phone_number': row['phone_number'],
        'broker': row['broker_id'],
        'ciiu': row['ciiu_id'],
        'type_client': row['type_client_id'],
        'type_identity': row['type_identity_id'],
        'department': row['department_id'],
        'city': row['city_id'],
        'birth_date': row['birth_date'],
    })

with open('newClients.json', 'w') as outfile:
    json.dump(data, outfile)