# Serializers
from apps.operation.api.serializers.preOperation.index import PreOperationReadOnlySerializer
from apps.administration.api.serializers.emitterDeposit.index import EmitterDepositNSSerializer
from apps.report.api.serializers.negotiationSummary.index import NegotiationSummarySerializer, NegotiationSummaryReadOnlySerializer
from apps.administration.api.serializers.accountingControl.index import AccountingControlSerializer
# Utils
from apps.base.utils.index import response, checkTypeIdentity, BaseAV
from django.template.loader import get_template
from apps.base.utils.index import response, BaseAV, gen_uuid, pdfToBase64
import requests
# Decorators
from apps.base.decorators.index import checkRole
# Models
from apps.operation.models import PreOperation
from apps.report.models import NegotiationSummary
from apps.client.models import RiskProfile
from apps.administration.models import EmitterDeposit, AccountingControl
from apps.client.models import LegalRepresentative
from apps.report.models import NegotiationSummary, PendingAccount
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



class NegotiationSummaryAV(BaseAV):
    @checkRole(['admin'])
    def get(self, request):
        try:
            if( request.query_params['id'] != 'undefined') and (len(request.query_params)== 1):
                data = {}
                operationId = []
                logger.debug(f'a {request.query_params}')
                # get the operation
                operation = PreOperation.objects.filter(opId=request.query_params['id'])
                # get the serializer
                serializer = PreOperationReadOnlySerializer(operation, many=True)
                # Prepare the data
                # emitter
                data['emitter'] = {
                'id': serializer.data[0]['emitter']['id'],
                'name': serializer.data[0]['emitter']['social_reason'] if serializer.data[0]['emitter']['social_reason'] else serializer.data[0]['emitter']['first_name'] + ' ' + serializer.data[0]['emitter']['last_name'],
                'typeDocument':  checkTypeIdentity(serializer.data[0]['emitter']['type_identity']),
                'typeClient': serializer.data[0]['emitter']['type_client'],
                'document': serializer.data[0]['emitter']['document_number'],
                 }
                #payer
                data['payer'] = {
                    'name': serializer.data[0]['payer']['social_reason'] if serializer.data[0]['payer']['social_reason'] else serializer.data[0]['payer']['first_name'] + ' ' + serializer.data[0]['payer']['last_name'],
                    'typeDocument':  checkTypeIdentity(serializer.data[0]['payer']['type_identity']),
                    'typeClient': serializer.data[0]['payer']['type_client'],
                    'document': serializer.data[0]['payer']['document_number'],
                }

                for x in serializer.data:
                    operationId.append(x['id'])

                # operation
                data['operation'] = {
                    'id': operationId,
                    'opId': serializer.data[0]['opId'],
                    'opDate': serializer.data[0]['opDate'],
                    'futureValue': 0,
                    'payedPercent': 'Ver Reporte de compra',
                    'valueToDiscount': 0,
                    'discountTax': serializer.data[0]['discountTax'],
                    'discountedDays':'Ver Reporte de compra',
                    'SMDiscount': 0,
                    'investorValue': 0,
                    'investorDiscount': 0,
                    'commissionValueBeforeTaxes': 0,
                    'operationValue': 0,
                    'tableCommission':0,
                    'iva': 0,
                    'retIva': 0,
                    'retIca': 0,
                    'retFte': 0,
                    'billValue':0
                }

                for x in serializer.data:
                    data['operation']['futureValue']     += x['amount']
                    data['operation']['valueToDiscount'] += x['payedAmount']
                    data['operation']['SMDiscount']      += x['presentValueSF']
                    data['operation']['investorValue']   += x['presentValueInvestor']

                data['operation']['investorDiscount'] = round(data['operation']['valueToDiscount'] - data['operation']['investorValue'])
                data['operation']['commissionValueBeforeTaxes'] = round(data['operation']['investorValue'] - data['operation']['SMDiscount'])
                if  data['operation']['commissionValueBeforeTaxes'] < 165000:
                     data['operation']['commissionValueBeforeTaxes'] = 165000
                data['operation']['operationValue'] =  round(data['operation']['investorDiscount'] + data['operation']['commissionValueBeforeTaxes'])
                data['operation']['tableCommission'] = round(data['operation']['investorValue']  - data['operation']['SMDiscount'])
                if data['operation']['tableCommission'] < 165000:
                    data['operation']['tableCommission'] = 165000

                data['operation']['iva'] = round(data['operation']['tableCommission'] * 0.19)
                # risk profile
                riskProfile = RiskProfile.objects.get(client=serializer.data[0]['emitter']['id'])
                if riskProfile.iva:
                    data['operation']['retIva'] = round(data['operation']['iva'] * 0.15)
                if riskProfile.ica:
                    data['operation']['retIca'] = round(data['operation']['tableCommission'] * 0.00966)

                if data['emitter']['typeClient'] == '21cf32d9-522c-43ac-b41c-4dfdf832a7b8':
                    data['operation']['retFte'] = round(data['operation']['tableCommission'] * 0.11)

                data['operation']['billValue'] = round(data['operation']['tableCommission'] +  data['operation']['iva'] - (
                    data['operation']['retIva'] + data['operation']['retIca'] + data['operation']['retFte']
                ))

                # emitter deposits
                emitterDeposits = EmitterDeposit.objects.filter(operation__opId=data['operation']['opId']).filter(state=1)
                serializer = EmitterDepositNSSerializer(emitterDeposits, many=True)
                data['emitterDeposits'] = serializer.data
            
            elif 'mode' in request.query_params and request.query_params['mode'] == 'query' and (request.query_params['id'] != 'undefined') and (len(request.query_params)==2):
                try:
                    logger.debug(f'bbbbbbbbbbbbbbbb')
                    data = NegotiationSummary.objects.get(opId=int(request.query_params['id']))
                    serializer = NegotiationSummaryReadOnlySerializer(data)
                    logger.debug(data)
                    return response({'error': False, 'data': serializer.data}, 200)
                except NegotiationSummary.DoesNotExist:
                    # Handle case when NegotiationSummary is not found
                    return response({'error': True, 'message': 'NegotiationSummary matching query does not exist.'}, 404)

            elif 'mode' in request.query_params and 'id' in request.query_params and  ('startDate' not in request.query_params) and ('endDate' not in request.query_params) and request.query_params['mode'] == 'filter' and (request.query_params['id'] != 'undefined') and (request.query_params['emitter'] == '') and (len(request.query_params)==3):
                try:
                    logger.debug(f'ccccccccccccccccccccccccccccccccc')
                    data = NegotiationSummary.objects.get(opId=int(request.query_params['id']))
                    serializer = NegotiationSummaryReadOnlySerializer(data)
                    logger.debug(data)
                    return response({'error': False, 'data': serializer.data}, 200)
                except NegotiationSummary.DoesNotExist:
                    # Handle case when NegotiationSummary is not found
                    return response({'error': True, 'message': 'NegotiationSummary matching query does not exist.'}, 404)
            elif 'mode' in request.query_params and 'emitter' in request.query_params and request.query_params['mode'] == 'filter'and ('startDate' not in request.query_params) and ('endDate' not in request.query_params) and (request.query_params['id'] == '') and (request.query_params['emitter'] != ''):
                    logger.debug('solo emisor')
                    try:
                        # Filtrar por el emisor de la solicitud
                        data = NegotiationSummary.objects.filter(
                            emitter__icontains=request.query_params['emitter'].upper(),
                            state=1
                        )
                        logger.debug(f'd {request.query_params}')
                        # Contar resultados filtrados
                        total_count = data.count()

                        # Instanciar el paginador
                        paginator = self.pagination_class()
                        page = paginator.paginate_queryset(data, request)
                     
                        # Si hay paginación, devolver datos paginados
                        if page is not None:
                            serializer = NegotiationSummaryReadOnlySerializer(page, many=True)
                            return paginator.get_paginated_response(serializer.data)

                        # Si no hay paginación, devolver todos los datos
                        serializer = NegotiationSummaryReadOnlySerializer(data, many=True)
                        return response({
                            'error': False, 
                            'data': serializer.data, 
                            'count': total_count
                        }, status=200)

                    except Exception as e:
                        # Manejo de errores
                        return response({'error': True, 'message': str(e)}, status=500)
                    
            elif 'mode' in request.query_params and 'startDate' in request.query_params and request.query_params['mode'] == 'filter' and (request.query_params['id'] == '') and (request.query_params['emitter'] == '' ) and (request.query_params['startDate']!= '') and (request.query_params['endDate'] != ''):
                    logger.debug('solo fecha')
                    try:
                        # Inicializar el filtro básico por estado
                        filters = {'state': 1}

                        # Verificar si 'startDate' está presente y filtrar por fecha de inicio
                        if 'startDate' in request.query_params and request.query_params['startDate']:
                            start_date = request.query_params['startDate']
                            filters['date__gte'] = start_date  # Filtrar desde la fecha de inicio

                        # Verificar si 'endDate' está presente y filtrar por fecha de fin
                        if 'endDate' in request.query_params and request.query_params['endDate']:
                            end_date = request.query_params['endDate']
                            filters['date__lte'] = end_date  # Filtrar hasta la fecha de fin

                        # Filtrar por los parámetros establecidos
                        data = NegotiationSummary.objects.filter(**filters)

                        # Contar los resultados filtrados
                        total_count = data.count()

                        # Instanciar el paginador
                        paginator = self.pagination_class()
                        page = paginator.paginate_queryset(data, request)

                        # Si hay paginación, devolver datos paginados
                        if page is not None:
                            serializer = NegotiationSummaryReadOnlySerializer(page, many=True)
                            return paginator.get_paginated_response(serializer.data)

                        # Si no hay paginación, devolver todos los datos
                        serializer = NegotiationSummaryReadOnlySerializer(data, many=True)
                        return response({
                            'error': False,
                            'data': serializer.data,
                            'count': total_count
                        }, status=200)

                    except Exception as e:
                        # Manejo de errores
                        return response({'error': True, 'message': str(e)}, status=500)

            elif ('mode' in request.query_params) and ('startDate' in request.query_params) and ('id' in request.query_params )and 'endDate' in request.query_params and (request.query_params['mode'] == 'filter') and (request.query_params['id'] != '') and (request.query_params['emitter'] == ''):
                logger.debug('filtro de id y fecha')
                try:
                    # Filtro básico por estado
                    filters = {'state': 1}

                    # Verificar si 'id' está presente y filtramos por ID
                    if 'id' in request.query_params and request.query_params['id']:
                        filters['id'] = request.query_params['id']  # Filtrar por ID

                    # Verificar si 'startDate' está presente y filtrar por fecha de inicio
                    if 'startDate' in request.query_params and request.query_params['startDate']:
                        start_date = request.query_params['startDate']
                        filters['date__gte'] = start_date  # Filtrar desde la fecha de inicio

                    # Verificar si 'endDate' está presente y filtrar por fecha de fin
                    if 'endDate' in request.query_params and request.query_params['endDate']:
                        end_date = request.query_params['endDate']
                        filters['date__lte'] = end_date  # Filtrar hasta la fecha de fin

                    # Filtrar por los parámetros establecidos
                    data = NegotiationSummary.objects.filter(**filters)

                    # Contar los resultados filtrados
                    total_count = data.count()

                    # Instanciar el paginador
                    paginator = self.pagination_class()
                    page = paginator.paginate_queryset(data, request)

                    # Si hay paginación, devolver datos paginados
                    if page is not None:
                        serializer = NegotiationSummaryReadOnlySerializer(page, many=True)
                        return paginator.get_paginated_response(serializer.data)

                    # Si no hay paginación, devolver todos los datos
                    serializer = NegotiationSummaryReadOnlySerializer(data, many=True)
                    return response({
                        'error': False,
                        'data': serializer.data,
                        'count': total_count
                    }, status=200)

                except Exception as e:
                    # Manejo de errores
                    return response({'error': True, 'message': str(e)}, status=500)
            elif 'mode' in request.query_params and 'emitter' in request.query_params and 'startDate' in request.query_params and 'endDate' in request.query_params and request.query_params['mode'] == 'filter' and (request.query_params['id'] == '') and request.query_params['emitter'] != '':
                logger.debug('filtro de emisor y fecha')
                try:
                    # Filtro básico por estado
                    filters = {'state': 1}

                    # Verificar si 'emitter' está presente y filtramos por emisor
                    if 'emitter' in request.query_params and request.query_params['emitter']:
                        filters['emitter__icontains'] = request.query_params['emitter']  # Filtrar por emisor

                    # Verificar si 'startDate' está presente y filtrar por fecha de inicio
                    if 'startDate' in request.query_params and request.query_params['startDate']:
                        start_date = request.query_params['startDate']
                        filters['date__gte'] = start_date  # Filtrar desde la fecha de inicio

                    # Verificar si 'endDate' está presente y filtrar por fecha de fin
                    if 'endDate' in request.query_params and request.query_params['endDate']:
                        end_date = request.query_params['endDate']
                        filters['date__lte'] = end_date  # Filtrar hasta la fecha de fin

                    # Filtrar por los parámetros establecidos
                    data = NegotiationSummary.objects.filter(**filters)

                    # Contar los resultados filtrados
                    total_count = data.count()

                    # Instanciar el paginador
                    paginator = self.pagination_class()
                    page = paginator.paginate_queryset(data, request)

                    # Si hay paginación, devolver datos paginados
                    if page is not None:
                        serializer = NegotiationSummaryReadOnlySerializer(page, many=True)
                        return paginator.get_paginated_response(serializer.data)

                    # Si no hay paginación, devolver todos los datos
                    serializer = NegotiationSummaryReadOnlySerializer(data, many=True)
                    return response({
                        'error': False,
                        'data': serializer.data,
                        'count': total_count
                    }, status=200)

                except Exception as e:
                    # Manejo de errores
                    return response({'error': True, 'message': str(e)}, status=500)

            elif request.query_params['pdf'] != 'undefined':
                
                logger.debug(f'e {request.query_params}')
                # get the operation 
                operation = PreOperation.objects.filter(opId=request.query_params['pdf'])
                serializer   = PreOperationReadOnlySerializer(operation, many=True)
                 #get the legal client of the emitter
                legalRepresentative = LegalRepresentative.objects.filter(client=operation[0].emitter.id)
                # get the negotiation Summary
                negotiationSummary = NegotiationSummary.objects.get(opId=request.query_params['pdf'])
                # get the emitter deposits
                emitterDeposits = EmitterDeposit.objects.filter(operation__opId=request.query_params['pdf'])
                # get the pending Accounts
                pendingAccounts = PendingAccount.objects.filter(opId=request.query_params['pdf'])
                data = {
                'sellReport':{
                    'opId': request.query_params['pdf'],
                    'operations': len(serializer.data),
                    'emitterName' : operation[0].emitter.first_name + ' ' + operation[0].emitter.last_name if operation[0].emitter.first_name else operation[0].emitter.social_reason,
                    'emitterDocumentNumber': operation[0].emitter.document_number,
                    'emitterTypeDocument': operation[0].emitter.type_identity.description,
                    'emitterAddress': operation[0].emitter.address,
                    'emitterEmail': operation[0].emitter.email,
                    'emitterPhoneNumber': operation[0].emitter.phone_number,
                    'emitterBroker': operation[0].emitter.broker.first_name + ' ' + operation[0].emitter.broker.last_name if operation[0].emitter.broker.first_name else operation[0].emitter.broker.social_reason,
                    'bills' : 0,
                    'sell' : 0,
                    'nominal': 0,
                    'future'    : 0,
                    'billsList' : [],
                    'legalRepresentative': legalRepresentative[0].first_name + ' ' + legalRepresentative[0].last_name if legalRepresentative[0].first_name else legalRepresentative[0].social_reason,
                    'legalRepresentativeDocumentNumber': legalRepresentative[0].document_number,
                    'legalRepresentativeTypeDocument': legalRepresentative[0].type_identity.description,
                    'legalRepresentativePhone': legalRepresentative[0].phone_number,
                    'legalRepresentativeEmail': legalRepresentative[0].email,
                },
                "negotiationSummary":{
                    'opId': negotiationSummary.opId,
                    'date':  operation[0].opDate,
                    'emitter': negotiationSummary.emitter,
                    'emitterId': negotiationSummary.emitterId,
                    'payer': negotiationSummary.payer,
                    'payerId': negotiationSummary.payerId,
                    'futureValue': round(negotiationSummary.futureValue),
                    'payedPercent': negotiationSummary.payedPercent,
                    'valueToDiscount': round(negotiationSummary.valueToDiscount),
                    'discountTax': negotiationSummary.discountTax,
                    'discountedDays': negotiationSummary.discountedDays,
                    'SMDiscount': round(negotiationSummary.SMDiscount),
                    'investorValue': round(negotiationSummary.investorValue),
                    'investorDiscount': round(negotiationSummary.investorDiscount),
                    'commissionValueBeforeTaxes': round(negotiationSummary.commissionValueBeforeTaxes),
                    'operationValue': round(negotiationSummary.operationValue),
                    'tableCommission': round(negotiationSummary.tableCommission),
                    'iva': round(negotiationSummary.iva),
                    'retIva': round(negotiationSummary.retIva),
                    'retIca': round(negotiationSummary.retIca),
                    'retFte': round(negotiationSummary.retFte),
                    'billValue': round(negotiationSummary.billValue),
                    'totalDiscounts': round(negotiationSummary.totalDiscounts),
                    'totalDeposits':round(negotiationSummary.totalDeposits),
                    'total' : round(negotiationSummary.total),
                    'pendingToDeposit': round(negotiationSummary.pendingToDeposit),
                    'observations': negotiationSummary.observations if negotiationSummary.observations else 'SIN OBSERVACIONES',
                    'billId': negotiationSummary.billId,
                    
                },
                'emitterDeposits': [],
                'pendingAccounts': [],
                }
                
                
                for x in serializer.data:
                    logger.debug(f'fecha buscada:{x["bill"]}')
                    # Buscar la PreOperation basada en bill_id
                    logger.debug(f'bill_id: {x["bill"]["id"]}')
                    bill_id = x["bill"]["id"]
                  
                    operation_billid= PreOperation.objects.filter(bill_id= bill_id)
        
                    # Obtener el campo opExpiration
                    
                    logger.debug(f'operation con el bill_id { operation_billid}')
                    logger.debug(f"fechas {x['opExpiration']}")
                    data['sellReport']['bills']  += 1
                    data['sellReport']['sell']  += int(x['presentValueInvestor'])
                    data['sellReport']['nominal'] += int(x['payedAmount'])
                    data['sellReport']['future']     += int(x['amount'])
                    data['sellReport']['billsList'].append({
                        'id': x['bill']['id'],
                        'dateOP': datetime.strptime(x['opDate'],'%Y-%m-%d').strftime('%d/%m/%Y'),
                        'probDate': x['probableDate'],
                        'dateExp':(
                        datetime.strptime(x['opExpiration'], '%Y-%m-%d').strftime('%d/%m/%Y')
                        if ' ' not in x['opExpiration']
                        else datetime.strptime(x['opExpiration'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
                    ),
                        'doc': 'FACT',
                        'number': x['bill']['billId'],
                        'emitter': x['bill']['emitterName'],
                        'payer': x['bill']['payerName'],
                        'invTax': x['investorTax'],
                        'daysOP': x['operationDays'],
                        'VRBuy': x['presentValueInvestor'],
                        'VRFuture': x['payedAmount'],
                        'totalGM': x['amount'],
                        'investor':x['investor'],
                        'Desc':x['payedPercent'],
                        'TasaDesc':x['discountTax'],
                        'billFraction':x['billFraction'],
                    })
                
                for x in emitterDeposits:
                    data['emitterDeposits'].append({
                        'beneficiary': x.beneficiary,
                        'bankAccount':f'{x.bank.description} - {x.accountNumber}',
                        'date': x.date,
                        'amount': x.amount,
                        'state':x.state,# este es el que permite tener los depositos que corresponden
                    })

                for x in pendingAccounts:
                    data['pendingAccounts'].append({
                        'description':x.description,
                        'amount': x.amount,
                        'date': x.date,
                    })
                logger.debug(f'aaaa')
                template = get_template('negotiationSummary.html')
                logger.debug(f'bbbb')

                # Asegúrate de que 'data' esté bien formado y sea un diccionario
                context = data if isinstance(data, dict) else {'data': data}
                html_content = template.render(context)  # Usar context en lugar de data directamente

                logger.debug(f'HTML content generated successfully')
                logger.debug(f'cccc')

                try:
                    # Convertir HTML a PDF (asegúrate de que pdfToBase64 esté definida)
                    parseBase64 = pdfToBase64(html_content)
                    
                    # Verificar que la respuesta tenga la estructura esperada
                    if 'pdf' in parseBase64:
                        pdf_base64 = parseBase64['pdf']
                        logger.debug(f'PDF generated successfully')
                        logger.debug(f'dddddd')
                        
                        return response({
                            'error': False, 
                            'pdf': pdf_base64,  # Usar directamente el base64, no .json()
                            'data': data
                        }, 200)
                    else:
                        logger.error(f"Estructura inesperada en parseBase64: {parseBase64}")
                        return response({
                            'error': True, 
                            'message': 'Formato de PDF incorrecto'
                        }, 500)

                except Exception as e:
                    logger.error(f"Error generating PDF: {str(e)}")
                    return response({
                        'error': True, 
                        'message': f'Error al generar PDF: {str(e)}'
                    }, 500)
            
            
            
            
            
            elif request.query_params['opId'] != 'undefined':
                logger.debug(f'ffffffffffff')
                data = NegotiationSummary.objects.get(opId = request.query_params['opId'])
                serializer = NegotiationSummaryReadOnlySerializer(data)
                logger.debug(f'h')
                return response({'error': False, 'data': serializer.data}, 200)
            else:
                data = NegotiationSummary.objects.filter(state = 1)
                logger.debug(f'g {request.query_params}')
                page = self.paginate_queryset(data)
                if page is not None:
                    serializer = NegotiationSummaryReadOnlySerializer(page, many=True)
                    return self.get_paginated_response(serializer.data)                

            return response({'error': False, 'data': data}, 200)
        except PreOperation.DoesNotExist:
            return response({'error': False, 'message':'la operacion no existe'}, 404)
        except RiskProfile.DoesNotExist:
            return response({'error': False, 'message':'El Cliente no posee perfil de riesgo'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, 500)



    @checkRole(['admin'])
    def post(self, request):
        try:
            serializer = NegotiationSummarySerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'message': 'Resumen de Negociación creado','data': request.data}, 200)
            else:
                return response({'error': True, 'message': serializer.errors}, 500)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, 500)

    @checkRole(['admin'])
    def delete(self, request, pk):
        try:
            data = NegotiationSummary.objects.get(pk=pk)
            data.delete()
            return response({'error': False, 'message': 'Resumen de Negociación eliminado'}, 200)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, 500)

    @checkRole(['admin'])
    def patch(self, request, pk):
        try:
            data = NegotiationSummary.objects.get(pk=pk)
            serializer = NegotiationSummarySerializer(data, data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'data': "Resumen de Negociación actualizado"}, 200)
            else:
                return response({'error': True, 'message': serializer.errors}, 500)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, 500)
