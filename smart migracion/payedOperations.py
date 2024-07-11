import pandas as pd
import uuid
import json
from datetime import datetime
import math
# Read the tablas.xlsx file and get the CORREDORES sheet
df = pd.read_excel('payedOperations.xlsx', sheet_name='Hoja 1')
# convert all rows to a list of dictionaries
data = df.to_dict('records')
operations = []
for row in data:
    operations.append({
        'op':row['NRO_OP'],
        'bill':str(row['NRO_FACT_OP']),
    })

# save in a json
with open('payedOperations.json', 'w') as json_file:
    json.dump(operations, json_file, indent=4)