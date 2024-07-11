# Serializers
from apps.operation.api.serializers.preOperation.index import PreOperationReadOnlySerializer
from apps.administration.api.serializers.emitterDeposit.index import EmitterDepositNSSerializer
from apps.report.api.serializers.negotiationSummary.index import NegotiationSummarySerializer, NegotiationSummaryReadOnlySerializer
from apps.administration.api.serializers.accountingControl.index import AccountingControlSerializer
# Utils
from apps.base.utils.index import response, checkTypeIdentity, BaseAV
from django.template.loader import get_template
import requests
# Decorators
from apps.base.decorators.index import checkRole
# Models
from apps.operation.models import PreOperation
from apps.client.models import RiskProfile
from apps.administration.models import EmitterDeposit, AccountingControl
from apps.client.models import LegalRepresentative
from apps.report.models import NegotiationSummary, PendingAccount



class NegotiationSummaryAV(BaseAV):
    @checkRole(['admin'])
    def get(self, request):
        try:
            if request.query_params['id'] != 'undefined':
                data = {}
                operationId = []
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
               
            elif request.query_params['pdf'] != 'undefined':
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
                    'operations': serializer.data,
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
                    'date': negotiationSummary.date,
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
                    'total' : round(negotiationSummary.total),
                    'pendingToDeposit': round(negotiationSummary.pendingToDeposit),
                    'observations': negotiationSummary.observations if negotiationSummary.observations else 'SIN OBSERVACIONES',
                },
                'emitterDeposits': [],
                'pendingAccounts': [],
                }
                for x in serializer.data:
                    data['sellReport']['bills']  += 1
                    data['sellReport']['sell']  += x['presentValueInvestor']
                    data['sellReport']['nominal'] += x['payedAmount']
                    data['sellReport']['future']     += x['amount']
                    data['sellReport']['billsList'].append({
                        'id': x['bill']['id'],
                        'dateOP': x['opDate'],
                        'probDate': x['probableDate'],
                        'dateExp': x['bill']['expirationDate'],
                        'doc': 'FACT',
                        'number': x['bill']['billId'],
                        'emitter': x['bill']['emitterName'],
                        'payer': x['bill']['payerName'],
                        'invTax': x['investorTax'],
                        'daysOP': x['operationDays'],
                        'VRBuy': x['presentValueInvestor'],
                        'VRFuture': x['payedAmount'],
                        'totalGM': x['amount']
                    })
                
                for x in emitterDeposits:
                    data['emitterDeposits'].append({
                        'beneficiary': x.beneficiary,
                        'bankAccount':f'{x.bank.description} - {x.accountNumber}',
                        'date': x.date,
                        'amount': x.amount,
                    })

                for x in pendingAccounts:
                    data['pendingAccounts'].append({
                        'description':x.description,
                        'amount': x.amount,
                        'date': x.date,
                    })
                
                template = get_template('negotiationSummary.html')
                test = template.render(data)
                pdf = requests.post('https://j2ncm3xeo7.execute-api.us-east-1.amazonaws.com/dev/api/html-to-pdf', json={'html': test})
                return response({'error': False, 'pdf': pdf.json()['pdf'], 'data': data}, 200)
            elif request.query_params['opId'] != 'undefined':
                data = NegotiationSummary.objects.get(id = request.query_params['opId'])
                serializer = NegotiationSummaryReadOnlySerializer(data)
                return response({'error': False, 'data': serializer.data}, 200)
            else:
                data = NegotiationSummary.objects.filter(state = 1)
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
