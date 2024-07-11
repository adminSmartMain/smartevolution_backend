import pandas as pd
import uuid
import json
df = pd.read_excel('newTables.xlsx', sheet_name='FACTURAS')
# convert all rows to a list of dictionaries
bills = df.to_dict('records')
parsedBills = []
counter = 0
for bill in bills:
    counter += 1
    parsedBills.append(bill['NRO_FACTURA'])
    #if bill['ESTADO'] == 'FV':
    #    typeBill = 'fdb5feb4-24e9-41fc-9689-31aff60b76c9'
    #elif bill['ESTADO'] == 'FV-TV':
    #    typeBill = 'a7c70741-8c1a-4485-8ed4-5297e54a978a'
    #else:
    #    typeBill = '29113618-6ab8-4633-aa8e-b3d6f242e8a4'
    #
    #expirationDate = bill['FECHA_VENCIMIENTO'].strftime('%Y-%m-%d')
    #dateBill       = bill['FECHA_EMISION'].strftime('%Y-%m-%d')
    #dataBill = {
    #    'id'              : str(uuid.uuid4()),
    #    'billId'          : bill['NRO_FACTURA'],
    #    'emitterId'       : bill['NIT_EMISOR'],
    #    'emitterName'     : bill['NOMBRE_EMISOR'],
    #    'payerId'         : bill['NIT_PAGADOR'],
    #    'payerName'       : bill['NOMBRE_PAGADOR'],
    #    'billValue'       : bill['VAL_RECIBIR'],
    #    'subTotal'        : bill['SUBTOTAL'],
    #    'total'           : bill['VAL_RECIBIR'],
    #    'currentBalance'  : 0,
    #    'cufe'            : bill['CUFE'] if bill['CUFE'] else None,
    #    'iva'             : bill['IVA'],
    #    'dateBill'        : dateBill,
    #    'datePayment'     : expirationDate,
    #    'expirationDate'  : expirationDate,
    #    'ret_fte'         : bill['AP_RET_FTE'],
    #    'ret_iva'         : bill['AP_RET_ICA'],
    #    'ret_ica'         : bill['AP_RET_IVA'],
    #    'creditNotesValue': bill['NOTAS'],
    #    'other_ret'       : bill['OTRAS_RET'],
    #    'typeBillId'      : typeBill,
    #}

    #parsedBills.append(dataBill)

with open('billsId.json', 'w') as outfile:
    json.dump(parsedBills, outfile)