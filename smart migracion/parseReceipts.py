import pandas as pd
import uuid
import json
from datetime import datetime
import math
# Read the tablas.xlsx file and get the CORREDORES sheet
df = pd.read_excel('receipts.xlsx', sheet_name='Hoja1')
# convert all rows to a list of dictionaries
data = df.to_dict('records')

receipts = []
counter = 0

for row in data:
    counter += 1
    id = str(uuid.uuid4())
    dId = counter
    data = str(row['date'])[:10]
    typeReceipt = row['typeReceipt_id']
    payedAmount = row['payedAmount']
    investorInterests = row['investorInterests']
    tableInterests = row['tableInterests']
    additionalDays = 0
    operation = row['operation_id']
    additionalInterests = row['additionalInterests']
    account = row['account_id']
    receiptStatus = row['receiptStatus_id']
    presentValueInvestor = row['presentValueInvestor']

    receipts.append({
        'id': id,
        'dId': dId,
        'data': data,
        'typeReceipt': typeReceipt,
        'payedAmount': payedAmount,
        'investorInterests': investorInterests,
        'tableInterests': tableInterests,
        'additionalDays': additionalDays,
        'operation': operation,
        'additionalInterests': additionalInterests,
        'account': account,
        'receiptStatus': receiptStatus,
        'presentValueInvestor': presentValueInvestor
    })


with open('parseReceipts.json', 'w') as outfile:
    json.dump(receipts, outfile, indent=4, sort_keys=True)