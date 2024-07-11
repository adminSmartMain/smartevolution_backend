# REST Framework imports
from rest_framework.decorators import APIView
# Serializers
from apps.operation.api.serializers.preOperation.index import PreOperationReadOnlySerializer
# Utils
from apps.base.utils.index import response
from django.template.loader import get_template
import requests
# Decorators
from apps.base.decorators.index import checkRole
# Models
from apps.operation.models import PreOperation
from apps.client.models import LegalRepresentative

class PurchaseOrderAV(APIView):
    @checkRole(['admin'])
    def get(self, request,pk):
        try:
            data = {}
            # Get the preOperation
            preOperation = PreOperation.objects.filter(opId=pk)
            serializer   = PreOperationReadOnlySerializer(preOperation, many=True)
            if request.GET.get('type') == 'investor':
                data = {
                    'opId': pk.replace('p-', ''),
                    'preOperations': serializer.data,
                    'investorName': preOperation[0].investor.first_name + ' ' + preOperation[0].investor.last_name if preOperation[0].investor.first_name else preOperation[0].investor.social_reason,
                    'investorDocumentNumber': preOperation[0].investor.document_number,
                    'investorAddress': preOperation[0].investor.address,
                    'investorEmail': preOperation[0].investor.email,
                    'investorPhoneNumber': preOperation[0].investor.phone_number,
                    'investorBroker': preOperation[0].investor.broker.first_name + ' ' + preOperation[0].investor.broker.last_name if preOperation[0].investor.broker.first_name else preOperation[0].investor.broker.social_reason,
                    'bills' : 0,
                    'total' : 0,
                    'future': 0,
                    'gm'    : 0,
                    'billsList' : []
                }
                for x in serializer.data:
                    data['bills']  += 1
                    data['total']  += x['payedAmount']
                    data['future'] += x['amount']
                    data['gm']     += x['GM']
                    data['billsList'].append({
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
                        'VRBuy': x['payedAmount'],
                        'VRFuture': x['amount'],
                        'totalGM': x['GM']
                    })
                #template = get_template('buyOrder-investor.html')
                #test = template.render(data)
                #pdf = requests.post('https://j2ncm3xeo7.execute-api.us-east-1.amazonaws.com/dev/api/html-to-pdf', json={'html': test})
                return response({'error': False, 'data':data}, 200)
            elif request.GET.get('type') == 'emitter':

                #get the legal client of the emitter
                legalRepresentative = LegalRepresentative.objects.filter(client=preOperation[0].emitter.id)
                data = {
                    'opId': pk,
                    'preOperations': serializer.data,
                    'emitterName' : preOperation[0].emitter.first_name + ' ' + preOperation[0].emitter.last_name if preOperation[0].emitter.first_name else preOperation[0].emitter.social_reason,
                    'emitterDocumentNumber': preOperation[0].emitter.document_number,
                    'emitterTypeDocument': preOperation[0].emitter.type_identity.description,
                    'emitterAddress': preOperation[0].emitter.address,
                    'emitterEmail': preOperation[0].emitter.email,
                    'emitterPhoneNumber': preOperation[0].emitter.phone_number,
                    'emitterBroker': preOperation[0].emitter.broker.first_name + ' ' + preOperation[0].emitter.broker.last_name if preOperation[0].emitter.broker.first_name else preOperation[0].emitter.broker.social_reason,
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
                }
                for x in serializer.data:
                    data['bills']  += 1
                    data['sell']  += x['presentValueInvestor']
                    data['nominal'] += x['payedAmount']
                    data['future']     += x['amount']
                    data['billsList'].append({
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
                template = get_template('new-buyOrder-emitter.html')
                test = template.render(data)
                pdf = requests.post('https://j2ncm3xeo7.execute-api.us-east-1.amazonaws.com/dev/api/html-to-pdf', json={'html': test})
                return response({'error': False, 'pdf': pdf.json()['pdf'], 'data': data}, 200)
            else:
                return response({'error': True, 'message': 'Tipo invalido'}, 400)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
