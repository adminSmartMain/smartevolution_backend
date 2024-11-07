from apps.report.utils.index import calcReportVariability
from apps.operation.api.serializers.index import PreOperationReadOnlySerializer
# Models
from apps.operation.models import PreOperation
from apps.client.models    import Client, FinancialCentral, Overview, LegalRepresentative
from apps.misc.models      import Activity
from apps.report.models import NegotiationSummary
from datetime import datetime
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
    
    
    logger.debug(f"legal Representative")
    
    # Get the legal representative of the investor
    legalRepresentative = LegalRepresentative.objects.get(client=investorId)
    
    # get operation emitter
    logger.debug(f"emitter")
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
    logger.debug(f"overviewEmitter")
    # parse the emitter financial central
    for item in financialCentralEmitter:
        
        
        dataFinancialCentralEmitter.append({
        'bank': item.bank.description,
        'centralBalances': item.centralBalances,
        'rating': item.rating
        })
    logger.debug(f"indicatorsEmitter")
    # calc the emitter indicators
    logger.debug(f"voy a hacer calcReportVariability")
    indicatorsEmitter = calcReportVariability(emitter.id,"","") 
    logger.debug(f" ya hice calcReportVariability")
    logger.debug(f"'variability': {indicatorsEmitter['emitter']['variability']}")
    #Procesar y estructurar la información financiera de un "emitter" (emisor) usando datos provenientes de un conjunto de diccionarios anidados. 
    try:
    #capturar cualquier tipo de error inesperado que ocurra mientras se procesan los datos.
        logger.debug(f"'variability': {indicatorsEmitter['emitter']['variability']}")
        
        dataEmitter = {
            'id': emitter.id,
            'name': f'{emitter.first_name} {emitter.last_name}' if emitter.first_name and emitter.last_name else emitter.social_reason,
            'documentNumber': emitter.document_number,
            'ciiu': emitter.ciiu.code if emitter.ciiu else '',
            'socialObject': '',
            'financialCentral': dataFinancialCentralEmitter,
            'qualitativeOverview': '',
            'financialAnalisis': '',
            'period_1': {},
            'period_2': {},
            'period_3': {},
            'variability': indicatorsEmitter['emitter']['variability']
        }
        #Dentro de cada periodo (period_1, period_2, period_3).
        # El código verifica si la clave de ese periodo existe antes de intentar acceder a sus valores. 
        try:
            # socialObject y qualitativeOverview/financialAnalisis
            if emitter.ciiu:
                dataEmitter['socialObject'] = Activity.objects.get(pk=emitter.ciiu.activity.id).description
            if overviewEmitter:
                dataEmitter['qualitativeOverview'] = overviewEmitter[0].qualitativeOverview
                dataEmitter['financialAnalisis'] = overviewEmitter[0].financialAnalisis

            # period_1, period_2, period_3
            for period_num in range(1, 4):
                period_key = f'period_{period_num}'
                if period_key in indicatorsEmitter['emitter']:
                    dataEmitter[period_key] = {
                        'period': indicatorsEmitter['emitter'][period_key].get('period', None),
                        'grossSale': indicatorsEmitter['emitter'][period_key].get('stateOfResult', {}).get('gross_sale', None),
                        'netSales': indicatorsEmitter['emitter'][period_key].get('stateOfResult', {}).get('net_sales', None),
                        'operatingProfit': indicatorsEmitter['emitter'][period_key].get('stateOfResult', {}).get('operating_profit', None),
                        'netIncome': indicatorsEmitter['emitter'][period_key].get('stateOfResult', {}).get('net_income', None),
                        'totalAssets': indicatorsEmitter['emitter'][period_key].get('assets', {}).get('total_assets', None),
                        'totalPassives': indicatorsEmitter['emitter'][period_key].get('passives', {}).get('total_passives', None),
                        'totalPatrimony': indicatorsEmitter['emitter'][period_key].get('patrimony', {}).get('total_patrimony', None),
                        'debt': indicatorsEmitter['emitter'][period_key].get('financialRisk', {}).get('debt', None),
                        'walletRotation': indicatorsEmitter['emitter'][period_key].get('activityEfficiency', {}).get('walletRotation', None),
                        'providersRotation': indicatorsEmitter['emitter'][period_key].get('activityEfficiency', {}).get('providersRotation', None),
                        #El cálculo de profitOverSales implica una división, lo que podría generar un ZeroDivisionError si el valor de net_sales es 0 o None. 
                        'profitOverSales': 0
                    }
                    
                    # Verificación de ZeroDivisionError
                    net_sales = dataEmitter[period_key]['netSales']
                    if net_sales not in (0, None):
                        dataEmitter[period_key]['profitOverSales'] = (dataEmitter[period_key]['operatingProfit'] / net_sales) * 100
        #Si ocurre cualquier error durante la ejecución, se captura y se registra mediante logger.error().
        except KeyError as e:
            logger.error(f"KeyError occurred while processing data for {period_key}: {e}")
        except AttributeError as e:
            logger.error(f"AttributeError occurred while processing data for {period_key}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
    #Este error se captura cuando se intenta acceder a una clave que no existe en un diccionario. 
    except KeyError as e:
        logger.error(f"KeyError when accessing indicatorsEmitter['emitter']: {e}")
    #Se captura si un objeto no tiene el atributo esperado, como si emitter.ciiu es None y se intenta acceder a .code. 
    except AttributeError as e:
        logger.error(f"AttributeError when accessing indicatorsEmitter['emitter']: {e}")
    #Se captura cualquier error no anticipado para garantizar que el programa no termine abruptamente. 
    except Exception as e:
        logger.error(f"Unexpected error while processing emitter data: {e}")


    logger.debug(f"'dataEmitter': {dataEmitter}")
    # payers data
   
    for x in setPayers:
        
        logger.debug(f"x in set payers {x}" )
        # get the payer
        payer = Client.objects.get(id=x)
        logger.debug(f"FinancialCentralPayer")
        # get the payer financial central
        financialCentralPayer = FinancialCentral.objects.filter(client=payer.id)
        
        # parse the emitter financial central
        try:
            
            for item in financialCentralPayer:
               
                dataFinancialCentralPayer.append({
                    'bank': item.bank.description,
                    'centralBalances': item.centralBalances,
                    'rating': item.rating
                })
                
        except ValueError as e:
        # Capturar el error y logear el mensaje de excepción
            logger.debug(f"error en el for: {e}")
        #get payer overview
        overviewPayer = Overview.objects.filter(client=payer.id)
       
        logger.debug(f"calculaReporteVariabilidad en pagadores")
        # calc the payer indicators
        indicatorsPayer = calcReportVariability("",x,None)
        
        logger.debug(f"calculado ReporteVariabilidad en pagadores")
        logger.debug(f"calculado ReporteVariabilidad en pagadores {indicatorsPayer}")
        try:
            logger.debug(f"entró al try")
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
                'profitOverSales'   : indicatorsPayer['payer']['period_1']['stateOfResult']['operating_profit'] / indicatorsPayer['payer']['period_1']['stateOfResult']['net_sales']*100 if indicatorsPayer['payer']['period_1']['stateOfResult']['net_sales'] not in (0,None) else 0
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
                'profitOverSales'   : indicatorsPayer['payer']['period_2']['stateOfResult']['operating_profit'] / indicatorsPayer['payer']['period_2']['stateOfResult']['net_sales']*100 if indicatorsPayer['payer']['period_2']['stateOfResult']['net_sales'] not in (0,None) else 0
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
                'profitOverSales'   : indicatorsPayer['payer']['period_3']['stateOfResult']['operating_profit'] / indicatorsPayer['payer']['period_3']['stateOfResult']['net_sales']*100 if indicatorsPayer['payer']['period_3']['stateOfResult']['net_sales'] not in (0,None) else 0
            } if 'period_3' in indicatorsPayer['payer'] else {},
            'variability': indicatorsPayer['payer']['variability']
                }
            
            logger.debug(f"dataPayer dentro del try de pagadores {dataPayer}")
        except:
            logger.debug(f"Except")
                
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
                    'profitOverSales'   : indicatorsPayer['payer']['period_1']['stateOfResult']['operating_profit'] / indicatorsPayer['payer']['period_1']['stateOfResult']['net_sales']*100 if indicatorsPayer['payer']['period_1']['stateOfResult']['net_sales'] not in (0,None) else 0
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
                        'profitOverSales'   : indicatorsPayer['payer']['period_1']['stateOfResult']['operating_profit'] / indicatorsPayer['payer']['period_1']['stateOfResult']['net_sales']*100 if indicatorsPayer['payer']['period_1']['stateOfResult']['net_sales'] not in (0,None) else 0
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
                        'profitOverSales'   : indicatorsPayer['payer']['period_2']['stateOfResult']['operating_profit'] / indicatorsPayer['payer']['period_2']['stateOfResult']['net_sales']*100 if indicatorsPayer['payer']['period_2']['stateOfResult']['net_sales'] not in (0,None) else 0
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
      
        # investor data  operation = PreOperation.objects.filter(opId=pk, investor=investorId)
       
        
        
        
        investor = {
            'opId': f'{prefix}{operation[0].opId}',
            #'investorValue': sum(operation[op].presentValueInvestor for op in range(0,len(operation))),
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
            dataOperation['total'] = y.presentValueInvestor + dataOperation['total']
            
            
            averageTerm += y.operationDays
            # get the operation bills
            bills.append({
                'id': y.bill.id,
                'dateOP': datetime.strptime(y.opDate.isoformat(), "%Y-%m-%d").strftime("%d/%m/%Y"),
                'probDate': datetime.strptime(y.probableDate.isoformat(), "%Y-%m-%d").strftime("%d/%m/%Y"),
                'dateExp': datetime.strptime(y.bill.expirationDate, "%Y-%m-%d").strftime("%d/%m/%Y"),
                'doc': 'FACT',
                'nroDoc': y.bill.billId,
                'number': y.bill.billId,
                'emitter': y.bill.emitterName,
                'payer': y.bill.payerName,
                'invTax': y.investorTax,
                'daysOP': y.operationDays,
                'VRBuy': round(y.presentValueInvestor),
                'VRFuture': round(y.payedAmount),
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
    