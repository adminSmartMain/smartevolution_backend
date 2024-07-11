from apps.report.utils.index import calcReportVariability
from apps.operation.api.serializers.index import PreOperationReadOnlySerializer
# Models
from apps.operation.models import PreOperation
from apps.client.models    import Client, FinancialCentral, Overview
from apps.misc.models      import Activity


def generateSellOffer(pk, prefix = ''):
    try:
            # variables
            payers = []
            dataFinancialCentralEmitter = []
            dataFinancialCentralPayer = []
            dataPayers = []
            bills = []
            totalBills = {
                'id':'',
                'total': 0,
                'future':0,
                'gm':0,
                'bills':0
            }
            investor = {
                'opId': "",
                'preOperations': "",
                'emitterName': "",
                'emitterDocumentNumber': "",
                'emitterAddress': "",
                'emitterEmail': "",
                'emitterPhoneNumber': "",
                'emitterBroker': "",
            }
            # get operation
            operation  = PreOperation.objects.filter(opId=pk)
            # get operation emitter
            emitter = Client.objects.get(id=operation[0].emitter.id)
            # get the operation payer/s
            for x in operation:
                payers.append(x.payer.id)
            # delete duplicates
            if len(payers) > 1:
                setPayers = list(dict.fromkeys(payers))
            else:
                setPayers = payers


            # get the emitter financial central
            financialCentralEmitter = FinancialCentral.objects.filter(client=emitter.id)
            #get emitter overview
            overviewEmitter = Overview.objects.filter(client=emitter.id)
            # parse the emitter financial central
            for item in financialCentralEmitter:
                dataFinancialCentralEmitter.append({
                'bank': item.bank.description,
                'centralBalances': item.centralBalances,
                'rating': item.rating
                })
            # calc the emitter indicators
            indicatorsEmitter = calcReportVariability(emitter.id,"","")
            # emitter data
            dataEmitter = {
                        'name': f'{emitter.first_name} {emitter.last_name}' if emitter.first_name and emitter.last_name else emitter.social_reason,
                        'documentNumber': emitter.document_number,
                        'ciiu': emitter.ciiu.code,
                        'socialObject': Activity.objects.get(pk=emitter.ciiu.activity.id).description,
                        'financialCentral': dataFinancialCentralEmitter,
                        'qualitativeOverview': overviewEmitter[0].qualitativeOverview,
                        'financialAnalisis': overviewEmitter[0].financialAnalisis,
                        'period_1': {
                            'period'         : indicatorsEmitter['emitter']['period_1']['period'],
                            'grossSale'      : indicatorsEmitter['emitter']['period_1']['stateOfResult']['gross_sale'],
                            'netSales'       : indicatorsEmitter['emitter']['period_1']['stateOfResult']['net_sales'],
                            'operatingProfit': indicatorsEmitter['emitter']['period_1']['stateOfResult']['operating_profit'],
                            'netIncome'      : indicatorsEmitter['emitter']['period_1']['stateOfResult']['net_income'],
                            'totalAssets'    : indicatorsEmitter['emitter']['period_1']['assets']['total_assets'],
                            'totalPassives'  : indicatorsEmitter['emitter']['period_1']['passives']['total_passives'],
                            'totalPatrimony' : indicatorsEmitter['emitter']['period_1']['patrimony']['total_patrimony'],
                            'debt'           : indicatorsEmitter['emitter']['period_1']['financialRisk']['debt'],
                            'walletRotation' : indicatorsEmitter['emitter']['period_1']['activityEfficiency']['walletRotation'],
                            'providersRotation' : indicatorsEmitter['emitter']['period_1']['activityEfficiency']['providersRotation'],
                        },
                        'period_2': {
                            'period'         : indicatorsEmitter['emitter']['period_2']['period'],
                            'grossSale'      : indicatorsEmitter['emitter']['period_2']['stateOfResult']['gross_sale'],
                            'netSales'       : indicatorsEmitter['emitter']['period_2']['stateOfResult']['net_sales'],
                            'operatingProfit': indicatorsEmitter['emitter']['period_2']['stateOfResult']['operating_profit'],
                            'netIncome'      : indicatorsEmitter['emitter']['period_2']['stateOfResult']['net_income'],
                            'totalAssets'    : indicatorsEmitter['emitter']['period_2']['assets']['total_assets'],
                            'totalPassives'  : indicatorsEmitter['emitter']['period_2']['passives']['total_passives'],
                            'totalPatrimony' : indicatorsEmitter['emitter']['period_2']['patrimony']['total_patrimony'],
                            'debt'           : indicatorsEmitter['emitter']['period_2']['financialRisk']['debt'],
                            'walletRotation' : indicatorsEmitter['emitter']['period_2']['activityEfficiency']['walletRotation'],
                            'providersRotation': indicatorsEmitter['emitter']['period_2']['activityEfficiency']['providersRotation'],
                        },
                        'period_3': {
                            'period'         : indicatorsEmitter['emitter']['period_3']['period'],
                            'grossSale'      : indicatorsEmitter['emitter']['period_3']['stateOfResult']['gross_sale'],
                            'netSales'       : indicatorsEmitter['emitter']['period_3']['stateOfResult']['net_sales'],
                            'operatingProfit': indicatorsEmitter['emitter']['period_3']['stateOfResult']['operating_profit'],
                            'netIncome'      : indicatorsEmitter['emitter']['period_3']['stateOfResult']['net_income'],
                            'totalAssets'    : indicatorsEmitter['emitter']['period_3']['assets']['total_assets'],
                            'totalPassives'  : indicatorsEmitter['emitter']['period_3']['passives']['total_passives'],
                            'totalPatrimony' : indicatorsEmitter['emitter']['period_3']['patrimony']['total_patrimony'],
                            'debt'           : indicatorsEmitter['emitter']['period_3']['financialRisk']['debt'],
                            'walletRotation' : indicatorsEmitter['emitter']['period_3']['activityEfficiency']['walletRotation'],
                            'providersRotation': indicatorsEmitter['emitter']['period_3']['activityEfficiency']['providersRotation'],
                        },
                        'variability': indicatorsEmitter['emitter']['variability']
            }
            # payer data
            for x in setPayers:
                # get the payer
                payer = Client.objects.get(id=x)
                # get the payer financial central
                financialCentralPayer = FinancialCentral.objects.filter(client=payer.id)
                # parse the emitter financial central
                for item in financialCentralPayer:
                    dataFinancialCentralPayer.append({
                        'bank': item.bank.description,
                        'centralBalances': item.centralBalances,
                        'rating': item.rating
                    })
                #get payer overview
                overviewPayer = Overview.objects.get(client=payer.id)

                # calc the payer indicators
                indicatorsPayer = calcReportVariability("",x,"")
                dataPayer = {
                    'name': f'{payer.first_name} {payer.last_name}' if payer.first_name and payer.last_name else payer.social_reason,
                    'documentNumber': payer.document_number,
                    'ciiu': payer.ciiu.code,
                    'socialObject': Activity.objects.get(pk=payer.ciiu.activity.id).description,
                    'financialCentral': dataFinancialCentralPayer,
                    'qualitativeOverview': overviewPayer.qualitativeOverview,
                    'financialAnalisis': overviewPayer.financialAnalisis,
                    'period_1': {
                        'period'            : indicatorsPayer['payer']['period_1']['period'],
                        'grossSale'         : indicatorsPayer['payer']['period_1']['stateOfResult']['gross_sale'],
                        'netSales'          : indicatorsPayer['payer']['period_1']['stateOfResult']['net_sales'],
                        'operatingProfit'   : indicatorsPayer['payer']['period_1']['stateOfResult']['operating_profit'],
                        'netIncome'         : indicatorsPayer['payer']['period_1']['stateOfResult']['net_income'],
                        'totalAssets'       : indicatorsPayer['payer']['period_1']['assets']['total_assets'],
                        'totalPassives'     : indicatorsPayer['payer']['period_1']['passives']['total_passives'],
                        'totalPatrimony'    : indicatorsPayer['payer']['period_1']['patrimony']['total_patrimony'],
                        'debt'              : indicatorsPayer['payer']['period_1']['financialRisk']['debt'],
                        'walletRotation'    : indicatorsPayer['payer']['period_1']['activityEfficiency']['walletRotation'],
                        'providersRotation' : indicatorsPayer['payer']['period_1']['activityEfficiency']['providersRotation'],
                    },
                    'period_2': {
                        'period'            : indicatorsPayer['payer']['period_2']['period'],
                        'grossSale'         : indicatorsPayer['payer']['period_2']['stateOfResult']['gross_sale'],
                        'netSales'          : indicatorsPayer['payer']['period_2']['stateOfResult']['net_sales'],
                        'operatingProfit'   : indicatorsPayer['payer']['period_2']['stateOfResult']['operating_profit'],
                        'netIncome'         : indicatorsPayer['payer']['period_2']['stateOfResult']['net_income'],
                        'totalAssets'       : indicatorsPayer['payer']['period_2']['assets']['total_assets'],
                        'totalPassives'     : indicatorsPayer['payer']['period_2']['passives']['total_passives'],
                        'totalPatrimony'    : indicatorsPayer['payer']['period_2']['patrimony']['total_patrimony'],
                        'debt'              : indicatorsPayer['payer']['period_2']['financialRisk']['debt'],
                        'walletRotation'    : indicatorsPayer['payer']['period_2']['activityEfficiency']['walletRotation'],
                        'providersRotation' : indicatorsPayer['payer']['period_2']['activityEfficiency']['providersRotation'],
                    },
                    'period_3': {
                        'period'            : indicatorsPayer['payer']['period_3']['period'],
                        'grossSale'         : indicatorsPayer['payer']['period_3']['stateOfResult']['gross_sale'],
                        'netSales'          : indicatorsPayer['payer']['period_3']['stateOfResult']['net_sales'],
                        'operatingProfit'   : indicatorsPayer['payer']['period_3']['stateOfResult']['operating_profit'],
                        'netIncome'         : indicatorsPayer['payer']['period_3']['stateOfResult']['net_income'],
                        'totalAssets'       : indicatorsPayer['payer']['period_3']['assets']['total_assets'],
                        'totalPassives'     : indicatorsPayer['payer']['period_3']['passives']['total_passives'],
                        'totalPatrimony'    : indicatorsPayer['payer']['period_3']['patrimony']['total_patrimony'],
                        'debt'              : indicatorsPayer['payer']['period_3']['financialRisk']['debt'],
                        'walletRotation'    : indicatorsPayer['payer']['period_3']['activityEfficiency']['walletRotation'],
                        'providersRotation' : indicatorsPayer['payer']['period_3']['activityEfficiency']['providersRotation'],
                    },
                    'variability': indicatorsPayer['payer']['variability']
                }
                # append the payer data
                dataPayers.append(dataPayer)
                dataOperation = {
                    'total': 0.0,
                    'averageTerm': 0.0,
                    'opType': operation[0].opType.description,
                    'opPendingAmount': operation[0].opPendingAmount,
                    'opDate': operation[0].opDate,
                    'discountTax': operation[0].discountTax,
                    'applyGm': operation[0].applyGm,
                    'opDays': operation[0].operationDays,
                }
                # investor data
                investor = {
                    'opId': f'{prefix}{operation[0].opId}',
                    'investor': operation[0].investor.first_name + ' ' + operation[0].investor.last_name if operation[0].investor.first_name else operation[0].investor.social_reason,
                    'investorId': operation[0].investor.id,
                    'investorDocumentNumber': operation[0].investor.document_number,
                    'investorAddress': operation[0].investor.address,
                    'investorEmail': operation[0].investor.email,
                    'investorPhoneNumber': operation[0].investor.phone_number,
                    'investorBroker': operation[0].investor.broker.first_name + ' ' + operation[0].investor.broker.last_name if operation[0].investor.broker.first_name else operation[0].investor.broker.social_reason,
                    'investorAccount': ''
                }

                # calc the operation details
            for y in operation:
                findDuplicates = [x for x in bills if x['number'] == y.bill.billId]
                if len(findDuplicates) == 0:
                    dataOperation['total'] = y.payedAmount + dataOperation['total']
                    dataOperation['averageTerm'] = y.operationDays + dataOperation['averageTerm']
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
                    dataOperation['averageTerm'] = int(dataOperation['averageTerm'] / len(operation))

            for x in bills:
                totalBills['total'] += x['VRBuy']
                totalBills['gm'] += x['totalGM']
                # verify if the bill id is in the list
                if x['id'] != totalBills['id']:
                    totalBills['future'] += x['VRFuture']
                totalBills['id'] = x['id']
                totalBills['bills'] = totalBills['bills'] + 1

            data = {
                'emitter': dataEmitter,
                'payers': dataPayers,
                'investor': investor,
                'operation': dataOperation,
                'bills': bills,
                'totalBills': totalBills,
                'centralsLength':len(dataFinancialCentralEmitter)
            } 

            return data
    except Exception as e:
        raise(e)