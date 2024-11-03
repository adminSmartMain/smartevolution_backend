from apps.report.utils.index import calcReportVariability
from apps.operation.api.serializers.index import PreOperationReadOnlySerializer
# Models
from apps.operation.models import PreOperation
from apps.client.models    import Client, FinancialCentral, Overview, LegalRepresentative
from apps.misc.models      import Activity
from apps.report.models import NegotiationSummary
from datetime import datetime


def generateSellOfferByInvestor(pk, investorId, prefix = ''):
    # Variables
    payers = []
    dataFinancialCentralEmitter = []
    dataFinancialCentralPayer = []
    dataPayers = []
    payersName = ""
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
        'legalRepresentativeName': "",
        'legalRepresentativeDocumentNumber': "",
    }
    # Get preOperations of the investor
    operation = PreOperation.objects.filter(opId=pk, investor=investorId)
    negotiationsummary = NegotiationSummary.objects.filter(opId=pk)
    
    # Get the legal representative of the investor
    legalRepresentative = LegalRepresentative.objects.get(client=investorId)
    # get operation emitter
    emitter = Client.objects.get(id=operation[0].emitter.id)
    # Get the operation payers
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
    # parse data of the emitter
    try:
         dataEmitter = {
                'id': emitter.id,
                'name': f'{emitter.first_name} {emitter.last_name}' if emitter.first_name and emitter.last_name else emitter.social_reason,
                'documentNumber': emitter.document_number,
                'ciiu': emitter.ciiu.code if emitter.ciiu else '',
                'socialObject'       : Activity.objects.get(pk=emitter.ciiu.activity.id).description if emitter.ciiu else '',
                'financialCentral'   : dataFinancialCentralEmitter,
                'qualitativeOverview': overviewEmitter[0].qualitativeOverview,
                'financialAnalisis'  : overviewEmitter[0].financialAnalisis,
                'period_1': {
                    'period'         : indicatorsEmitter['emitter']['period_1']['period'],#checked
                    'grossSale'      : indicatorsEmitter['emitter']['period_1']['stateOfResult']['gross_sale'],#checked
                    'netSales'       : indicatorsEmitter['emitter']['period_1']['stateOfResult']['net_sales'],#checked
                    'operatingProfit': indicatorsEmitter['emitter']['period_1']['stateOfResult']['operating_profit'],#checked
                    'netIncome'      : indicatorsEmitter['emitter']['period_1']['stateOfResult']['net_income'],#checked
                    'totalAssets'    : indicatorsEmitter['emitter']['period_1']['assets']['total_assets'],#checked
                    'totalPassives'  : indicatorsEmitter['emitter']['period_1']['passives']['total_passives'],#checked
                    'totalPatrimony' : indicatorsEmitter['emitter']['period_1']['patrimony']['total_patrimony'],#checked
                    'debt'           : indicatorsEmitter['emitter']['period_1']['financialRisk']['debt'],#checked
                    'walletRotation' : indicatorsEmitter['emitter']['period_1']['activityEfficiency']['walletRotation'],#checked
                    'providersRotation' : indicatorsEmitter['emitter']['period_1']['activityEfficiency']['providersRotation'],#checked
                    'profitOverSales': round(indicatorsEmitter['emitter']['period_1']['stateOfResult']['operating_profit'] /indicatorsEmitter['emitter']['period_1']['stateOfResult']['net_sales']) if indicatorsEmitter['emitter']['period_1']['stateOfResult']['operating_profit'] is not None and indicatorsEmitter['emitter']['period_1']['stateOfResult']['net_sales'] not in (None, 0) else 0

                } if 'period_1' in indicatorsEmitter['emitter'] else {},
                'period_2': {
                    'period'         : indicatorsEmitter['emitter']['period_2']['period'],#checked
                    'grossSale'      : indicatorsEmitter['emitter']['period_2']['stateOfResult']['gross_sale'],#checked
                    'netSales'       : indicatorsEmitter['emitter']['period_2']['stateOfResult']['net_sales'],#checked
                    'operatingProfit': indicatorsEmitter['emitter']['period_2']['stateOfResult']['operating_profit'],#checked
                    'netIncome'      : indicatorsEmitter['emitter']['period_2']['stateOfResult']['net_income'],#checked
                    'totalAssets'    : indicatorsEmitter['emitter']['period_2']['assets']['total_assets'],#checked
                    'totalPassives'  : indicatorsEmitter['emitter']['period_2']['passives']['total_passives'],#checked
                    'totalPatrimony' : indicatorsEmitter['emitter']['period_2']['patrimony']['total_patrimony'],#checked
                    'debt'           : indicatorsEmitter['emitter']['period_2']['financialRisk']['debt'],#checked
                    'walletRotation' : indicatorsEmitter['emitter']['period_2']['activityEfficiency']['walletRotation'],#checked
                    'providersRotation' : indicatorsEmitter['emitter']['period_2']['activityEfficiency']['providersRotation'],#checked
                    'profitOverSales': round(indicatorsEmitter['emitter']['period_2']['stateOfResult']['operating_profit'] /indicatorsEmitter['emitter']['period_1']['stateOfResult']['net_sales']) if indicatorsEmitter['emitter']['period_1']['stateOfResult']['operating_profit'] is not None and indicatorsEmitter['emitter']['period_1']['stateOfResult']['net_sales'] not in (None, 0) else 0

                } if 'period_2' in indicatorsEmitter['emitter'] else {},
                'period_3':  {
                    'period'         : indicatorsEmitter['emitter']['period_3']['period'],#checked
                    'grossSale'      : indicatorsEmitter['emitter']['period_3']['stateOfResult']['gross_sale'],#checked
                    'netSales'       : indicatorsEmitter['emitter']['period_3']['stateOfResult']['net_sales'],#checked
                    'operatingProfit': indicatorsEmitter['emitter']['period_3']['stateOfResult']['operating_profit'],#checked
                    'netIncome'      : indicatorsEmitter['emitter']['period_3']['stateOfResult']['net_income'],#checked
                    'totalAssets'    : indicatorsEmitter['emitter']['period_3']['assets']['total_assets'],#checked
                    'totalPassives'  : indicatorsEmitter['emitter']['period_3']['passives']['total_passives'],#checked
                    'totalPatrimony' : indicatorsEmitter['emitter']['period_3']['patrimony']['total_patrimony'],#checked
                    'debt'           : indicatorsEmitter['emitter']['period_3']['financialRisk']['debt'],#checked
                    'walletRotation' : indicatorsEmitter['emitter']['period_3']['activityEfficiency']['walletRotation'],#checked
                    'providersRotation' : indicatorsEmitter['emitter']['period_3']['activityEfficiency']['providersRotation'],#checked
                    'profitOverSales': round(indicatorsEmitter['emitter']['period_3']['stateOfResult']['operating_profit'] /indicatorsEmitter['emitter']['period_1']['stateOfResult']['net_sales']) if indicatorsEmitter['emitter']['period_1']['stateOfResult']['operating_profit'] is not None and indicatorsEmitter['emitter']['period_1']['stateOfResult']['net_sales'] not in (None, 0) else 0

                } if 'period_3' in indicatorsEmitter['emitter'] else {},
                'variability': indicatorsEmitter['emitter']['variability']
            }
    except :
            dataEmitter = {
                'id': emitter.id,
                'name': f'{emitter.first_name} {emitter.last_name}' if emitter.first_name and emitter.last_name else emitter.social_reason,
                'documentNumber': emitter.document_number,
                'ciiu': emitter.ciiu.code if emitter.ciiu else '',
                'socialObject'       : Activity.objects.get(pk=emitter.ciiu.activity.id).description if emitter.ciiu else '',
                'financialCentral'   : dataFinancialCentralEmitter,
                'qualitativeOverview': overviewEmitter[0].qualitativeOverview if overviewEmitter else '',
                'financialAnalisis'  : overviewEmitter[0].financialAnalisis if overviewEmitter else '',
                }
    # payers data
    
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
        overviewPayer = Overview.objects.filter(client=payer.id)
        # calc the payer indicators
        indicatorsPayer = calcReportVariability("",x,None)
        
        try:
            
            dataPayer = {
            'name': f'{payer.first_name} {payer.last_name}' if payer.first_name else payer.social_reason,
            'documentNumber': payer.document_number,
            'ciiu': payer.ciiu.code if payer.ciiu else '',
            'socialObject': Activity.objects.get(pk=payer.ciiu.activity.id).description if payer.ciiu else '',
            'financialCentral': dataFinancialCentralPayer,
            'qualitativeOverview': overviewPayer[0].qualitativeOverview if overviewPayer else '',
            'financialAnalisis': overviewPayer[0].financialAnalisis if overviewPayer else '',
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
                'profitOverSales'   : round(indicatorsPayer['payer']['period_1']['stateOfResult']['operating_profit'] / indicatorsPayer['payer']['period_1']['stateOfResult']['net_sales'])
            } if 'period_1' in indicatorsPayer['payer'] else {},
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
                'profitOverSales'   : round(indicatorsPayer['payer']['period_2']['stateOfResult']['operating_profit'] / indicatorsPayer['payer']['period_2']['stateOfResult']['net_sales'])
            } if 'period_2' in indicatorsPayer['payer'] else {},
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
                'profitOverSales'   : round(indicatorsPayer['payer']['period_3']['stateOfResult']['operating_profit'] / indicatorsPayer['payer']['period_3']['stateOfResult']['net_sales'])
            } if 'period_3' in indicatorsPayer['payer'] else {},
            'variability': indicatorsPayer['payer']['variability']
                }
        except:
                
                # check if indicators payer has the 3 periods(period_1 period_2 period_3) different to {} empty
                periods = 0
                if 'period_1' in indicatorsPayer['payer'] and 'period_2' in indicatorsPayer['payer']:
                    
                    if indicatorsPayer['payer']['period_1']['activityEfficiency'] != {} and indicatorsPayer['payer']['period_1']['activityEfficiency'] == {}:
                        
                        periods = 1
                    elif indicatorsPayer['payer']['period_2']['activityEfficiency'] != {}:
                        
                        periods = 2                 
                # check each period if is empty
               
                if periods == 1:
                    dataPayer = {
            'name': f'{payer.first_name} {payer.last_name}' if payer.first_name else payer.social_reason,
            'documentNumber': payer.document_number,
            'ciiu': payer.ciiu.code if payer.ciiu else '',
            'socialObject': Activity.objects.get(pk=payer.ciiu.activity.id).description if payer.ciiu else '',
            'financialCentral': dataFinancialCentralPayer,
            'qualitativeOverview': overviewPayer[0].qualitativeOverview if overviewPayer else '',
            'financialAnalisis': overviewPayer[0].financialAnalisis if overviewPayer else '',
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
                'profitOverSales'   : round(indicatorsPayer['payer']['period_1']['stateOfResult']['operating_profit'] / indicatorsPayer['payer']['period_1']['stateOfResult']['net_sales'])
            }if 'period_1' in indicatorsPayer['payer'] else {},
            'variability': indicatorsPayer['payer']['variability']
                }
                elif periods == 2:
                    
                     dataPayer = {
            'name': f'{payer.first_name} {payer.last_name}' if payer.first_name else payer.social_reason,
            'documentNumber': payer.document_number,
            'ciiu': payer.ciiu.code if payer.ciiu else '',
            'socialObject': Activity.objects.get(pk=payer.ciiu.activity.id).description if payer.ciiu else '',
            'financialCentral': dataFinancialCentralPayer,
            'qualitativeOverview': overviewPayer[0].qualitativeOverview if overviewPayer else '',
            'financialAnalisis': overviewPayer[0].financialAnalisis if overviewPayer else '',
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
                'profitOverSales'   : round(indicatorsPayer['payer']['period_1']['stateOfResult']['operating_profit'] / indicatorsPayer['payer']['period_1']['stateOfResult']['net_sales'])
            } if 'period_1' in indicatorsPayer['payer'] else {},
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
                'profitOverSales'   : round(indicatorsPayer['payer']['period_2']['stateOfResult']['operating_profit'] / indicatorsPayer['payer']['period_2']['stateOfResult']['net_sales'])
            }if 'period_2' in indicatorsPayer['payer'] else {},
            'variability': indicatorsPayer['payer']['variability']
                }
                else:
                     
                     dataPayer = {
                        'name': f'{payer.first_name} {payer.last_name}' if payer.first_name else payer.social_reason,
                        'documentNumber': payer.document_number,
                        'ciiu': payer.ciiu.code if payer.ciiu else '',
                        'socialObject': Activity.objects.get(pk=payer.ciiu.activity.id).description if payer.ciiu else '',
                        'financialCentral': dataFinancialCentralPayer,
                        'qualitativeOverview': overviewPayer[0].qualitativeOverview if overviewPayer else '',
                        'financialAnalisis': overviewPayer[0].financialAnalisis if overviewPayer else '',
                     }
        # append the payer data
        dataPayers.append(dataPayer)
      # Append the payer name to the payersName variable
        payersName = payersName + dataPayer['name'] + ', '
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
            'investorValue': negotiationsummary[0].investorValue,
            'investor': operation[0].investor.first_name + ' ' + operation[0].investor.last_name if operation[0].investor.first_name else operation[0].investor.social_reason,
            'investorId': operation[0].investor.id,
            'investorType':operation[0].investor.type_client.description,
            'investorBalance':round(operation[0].clientAccount.balance),
            'investorTypeDocument':operation[0].investor.type_identity.abbreviation,
            'investorDocumentNumber': operation[0].investor.document_number,
            'investorAddress': operation[0].investor.address,
            'investorEmail': operation[0].investor.email,
            'investorPhoneNumber': operation[0].investor.phone_number,
            'investorBroker': operation[0].investor.broker.first_name + ' ' + operation[0].investor.broker.last_name if operation[0].investor.broker.first_name else operation[0].investor.broker.social_reason,
            'legalRepresentativeName': legalRepresentative.first_name + ' ' + legalRepresentative.last_name if legalRepresentative.first_name else legalRepresentative.social_reason,
            'legalRepresentativeDocumentNumber': legalRepresentative.document_number,
            'legalRepresentativeTypeDocument':legalRepresentative.type_identity.abbreviation,
            'legalRepresentativePhone': legalRepresentative.phone_number,
            'legalRepresentativeEmail': legalRepresentative.email,
        }
        # calc the operation details
        averageTerm = 0
        for y in operation:
            findDuplicates = [x for x in bills if x['number'] == y.bill.billId]
            
            if len(findDuplicates) == 0:
                dataOperation['total'] = y.payedAmount + dataOperation['total']
                averageTerm += y.operationDays
                # get the operation bills
                bills.append({
                    'id': y.bill.id,
                    'dateOP': datetime.strptime(y.opDate.isoformat(), "%Y-%m-%d").strftime("%Y/%m/%d"),
                    'probDate': datetime.strptime(y.probableDate.isoformat(), "%Y-%m-%d").strftime("%Y/%m/%d"),
                    'dateExp': datetime.strptime(y.bill.expirationDate, "%Y-%m-%d").strftime("%Y/%m/%d"),
                    'doc': 'FACT',
                    'nroDoc': y.bill.billId,
                    'number': y.bill.billId,
                    'emitter': y.bill.emitterName,
                    'payer': y.bill.payerName,
                    'invTax': y.investorTax,
                    'daysOP': y.operationDays,
                    'VRBuy': round(y.payedAmount),
                    'VRFuture': round(y.amount),
                    'totalGM': round(y.GM)
                })
        # calc the average term
        dataOperation['averageTerm'] = round(averageTerm / len(operation))
        dataOperation['total'] = round(dataOperation['total'])

        for x in bills:
                totalBills['total'] += x['VRBuy']
                totalBills['gm'] += x['totalGM']
                # verify if the bill id is in the list
                if x['id'] != totalBills['id']:
                    totalBills['future'] += x['VRFuture']
                totalBills['id'] = x['id']
                totalBills['bills'] = totalBills['bills'] + 1

        # round each total of the bills
        totalBills['total'] = round(totalBills['total'])
        totalBills['gm'] = round(totalBills['gm'])
        totalBills['future'] = round(totalBills['future'])
    
    data = {
        'emitter': dataEmitter,
        'payers': dataPayers,
        'payersName': payersName[:-2],
        'investor': investor,
        'operation': dataOperation,
        'bills': bills,
        'totalBills': totalBills,
        'centralsLength':len(dataFinancialCentralEmitter),
        'legalRepresentative': legalRepresentative.first_name + ' ' + legalRepresentative.last_name if legalRepresentative.first_name else legalRepresentative.social_reason,
        'legalRepresentativeEmail': legalRepresentative.email,
        'legalRepresentativePhone': legalRepresentative.phone_number,
    } 

    return data
    