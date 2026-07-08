from apps.operation.api.serializers.index import PreOperationReadOnlySerializer
from django.db.models import Q
# Models
from apps.operation.models import PreOperation
from apps.client.models    import Client, FinancialCentral, Overview,Account
from apps.misc.models      import Activity


import logging

# Configurar el logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Crear un handler de consola y definir el nivel
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Crear un formato para los mensajes de log
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Añadir el handler al logger
logger.addHandler(console_handler)


def calcOperationDetail(pk, investorId):
    payers    = []
    setPayers = []
    bills     = []

    data = {
        'emitter':{
            'name': '',
            'document':''
        },
        'investor': {
            'investorId':'',
            'investor':'',
            'investorDocumentNumber':'',
            'investorPhoneNumber':'',
            'investorAccount':'',
            'investorAccountNumber':'',
            'investorAccountBalance':'',
        },
        'bills': {
            'averageTerm':0,
            'bills':0,
            'total':0
        },
        'payers': []
    }

     # get operation
    operation  = PreOperation.objects.filter(opId=pk, investor=investorId).filter(Q(status=0) | Q(status=1))
    operation_sum  = PreOperation.objects.filter(opId=pk, investor=investorId).filter(Q(status=1))
    investorAccountBalancesperOperation= Account.objects.filter(client_id=investorId).filter(Q(state=1))

    # get operation emitter
    emitter = Client.objects.get(id=operation[0].emitter.id)
    # set the emitter data
    data['emitter']['name'] = f'{emitter.first_name} {emitter.last_name}' if emitter.first_name and emitter.last_name else emitter.social_reason
    data['emitter']['document'] = emitter.document_number
    # get operation investor
    investor = Client.objects.get(id=operation[0].investor.id)
    # set the investor data
    data['investor']['investorId'] = operation[0].investor.id
    data['investor']['investor'] = f'{investor.first_name} {investor.last_name}' if investor.first_name else investor.social_reason
    data['investor']['investorDocumentNumber'] = investor.document_number
    data['investor']['investorPhoneNumber'] = investor.phone_number
    data['investor']['investorAccount'] = operation[0].clientAccount.id
    data['investor']['investorAccountNumber'] = operation[0].clientAccount.account_number
    data['investor']['investorAccountBalance'] = sum(op.balance for op in  investorAccountBalancesperOperation)

    # get the operation bills
    operationDays = 0
    for y in operation:
        findDuplicates = [x for x in bills if x['number'] == y.bill.billId]
        if len(findDuplicates) == 0:
            operationDays += y.operationDays
            data['bills']['averageTerm'] = y.operationDays + data['bills']['averageTerm']
            # get the operation bills
            bills.append({
                'id': y.bill.id,
                'dateOP': y.opDate.isoformat(),
                'probDate': y.probableDate.isoformat(),
                'dateExp': y.bill.expirationDate,
                'doc': 'FACT',
                'number': y.bill.billId,
                'emitter': y.bill.emitterName,
                'payer': y.bill.payerName,
                'invTax': y.investorTax,
                'daysOP': y.operationDays,
                'VRBuy': y.payedAmount,
                'VRFuture': y.amount,
                'totalGM': y.GM
                })


    data['bills']['bills'] = len(bills)

    for x in bills:
        data['bills']['total'] += x['VRBuy']

    # get the operation payer/s
    for x in operation:
        payers.append(x.payer.id)
    # delete duplicates
    if len(payers) > 1:
        setPayers = list(dict.fromkeys(payers))
    else:
        setPayers = payers

    data['bills']['averageTerm'] = operationDays / data['bills']['bills']

    # payer data
    for x in setPayers:
        payer = Client.objects.get(id=x)
        data['payers'].append({
            'name': f'{payer.first_name} {payer.last_name}' if payer.first_name else payer.social_reason,
            'documentNumber': payer.document_number,
    })

    return data