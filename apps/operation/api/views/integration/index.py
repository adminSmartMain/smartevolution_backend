# Rest framework
from rest_framework.generics import GenericAPIView

# Models 
from apps.report.api.models.index import NegotiationSummary
from apps.operation.api.models.index import PreOperation, BuyOrder, IntegrationHistory
from apps.administration.models import EmitterDeposit
from apps.client.models import LegalRepresentative
from apps.report.models import NegotiationSummary, PendingAccount
# Serializers
from apps.operation.api.serializers.preOperation.index import PreOperationReadOnlySerializer

# Utils
from apps.base.utils.index import response, pdfToBase64, gen_uuid
from django.template.loader import get_template
from base64 import b64decode
from apps.report.utils.index import getSignatureStatus
import requests
import os
from base64 import b64decode


class OperationIntegrationAV(GenericAPIView):

    def post(self, request):
        try:
            # Get the operations with the bills who has the same integrationCode
            operations = PreOperation.objects.filter(bill__integrationCode=request.data['integrationCode'])
            # get the buy order code from one of the operations
            code = ""
            route = ""
            investor = ""
            opId = 0
            for operation in operations:
                try:
                    buyOrder = BuyOrder.objects.get(operation=operation.id)
                    code = buyOrder.code
                    opId = operation.opId
                    investor = operation.investor.social_reason if operation.investor.social_reason else operation.investor.first_name + " " + operation.investor.last_name
                    break
                except:
                    pass

            signature = getSignatureStatus(code)
            # check if the status is finish
            if signature['message']['status'] != 'FINISH':
                return response({'error': False, 'message': 'La operación aun no esta aprobada'}, 200)

            operation = PreOperation.objects.filter(opId=opId)
            serializer   = PreOperationReadOnlySerializer(operation, many=True)
            # get the legal client of the emitter
            legalRepresentative = LegalRepresentative.objects.filter(client=operation[0].emitter.id)
            # get the negotiation Summary
            negotiationSummary = NegotiationSummary.objects.get(opId=opId)
            # get the emitter deposits
            emitterDeposits = EmitterDeposit.objects.filter(operation__opId=opId)
            # get the pending Accounts
            pendingAccounts = PendingAccount.objects.filter(opId=opId)
            data = {
            'sellReport':{
                'opId': opId,
                'operations': serializer.data,
                'emitterName' : operation[0].emitter.first_name + ' ' + operation[0].emitter.last_name if operation[0].emitter.first_name else operation[0].emitter.social_reason,
                'emitterDocumentNumber': operation[0].emitter.document_number,
                'emitterTypeDocument': operation[0].emitter.type_identity.description,
                'emitterAddress': operation[0].emitter.address,
                'emitterEmail': operation[0].emitter.email,
                'emitterPhoneNumber': operation[0].emitter.phone_number,
                'emitterBroker': operation[0].emitter.broker.first_name + ' ' + operation[0].emitter.broker.last_name if operation[0].emitter.broker.first_name else operation[0].emitter.broker.social_reason,
                'bills' : 0,
                'sell': negotiationSummary.settledInvestorValue if negotiationSummary.settledInvestorValue is not None else negotiationSummary.investorValue,
                'nominal': negotiationSummary.settledValueToDiscount if negotiationSummary.settledValueToDiscount is not None else negotiationSummary.valueToDiscount,
                'future': negotiationSummary.settledFutureValue if negotiationSummary.settledFutureValue is not None else negotiationSummary.futureValue,
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
                'futureValue': negotiationSummary.settledFutureValue if negotiationSummary.settledFutureValue is not None else negotiationSummary.futureValue,
                'payedPercent': negotiationSummary.payedPercent,
                'valueToDiscount': negotiationSummary.settledValueToDiscount if negotiationSummary.settledValueToDiscount is not None else negotiationSummary.valueToDiscount,
                'discountTax': negotiationSummary.discountTax,
                'discountedDays': negotiationSummary.discountedDays,
                'SMDiscount': negotiationSummary.settledSMDiscount if negotiationSummary.settledSMDiscount is not None else negotiationSummary.SMDiscount,
                'investorValue': negotiationSummary.settledInvestorValue if negotiationSummary.settledInvestorValue is not None else negotiationSummary.investorValue,
                'investorDiscount': negotiationSummary.settledInvestorDiscount if negotiationSummary.settledInvestorDiscount is not None else negotiationSummary.investorDiscount,
                'commissionValueBeforeTaxes': negotiationSummary.settledCommissionValueBeforeTaxes if negotiationSummary.settledCommissionValueBeforeTaxes is not None else negotiationSummary.commissionValueBeforeTaxes,
                'operationValue': negotiationSummary.settledOperationValue if negotiationSummary.settledOperationValue is not None else negotiationSummary.operationValue,
                'tableCommission': negotiationSummary.settledTableCommission if negotiationSummary.settledTableCommission is not None else negotiationSummary.tableCommission,
                'iva': negotiationSummary.settledIva if negotiationSummary.settledIva is not None else negotiationSummary.iva,
                'retIva': negotiationSummary.settledRetIva if negotiationSummary.settledRetIva is not None else negotiationSummary.retIva,
                'retIca': negotiationSummary.settledRetIca if negotiationSummary.settledRetIca is not None else negotiationSummary.retIca,
                'retFte': negotiationSummary.settledRetFte if negotiationSummary.settledRetFte is not None else negotiationSummary.retFte,
                'billValue': negotiationSummary.settledBillValue if negotiationSummary.settledBillValue is not None else negotiationSummary.billValue,
                'totalDiscounts': negotiationSummary.settledTotalDiscounts if negotiationSummary.settledTotalDiscounts is not None else negotiationSummary.totalDiscounts,
                'total': negotiationSummary.settledTotal if negotiationSummary.settledTotal is not None else negotiationSummary.total,
                'pendingToDeposit': negotiationSummary.settledPendingToDeposit if negotiationSummary.settledPendingToDeposit is not None else negotiationSummary.pendingToDeposit,
                'observations': negotiationSummary.observations if negotiationSummary.observations else 'SIN OBSERVACIONES',
            },
            'emitterDeposits': [],
            'pendingAccounts': [],
            }
            for x in serializer.data:
                data['sellReport']['bills']  += 1
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
                    'VRBuy': x['settledPresentValueInvestor'] if x['settledPresentValueInvestor'] is not None else x['presentValueInvestor'],
                    'VRFuture': x['settledPayedAmount'] if x['settledPayedAmount'] is not None else x['payedAmount'],
                    'totalGM': x['settledGM'] if x['settledGM'] is not None else x['GM']
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
            data = template.render(data)
            parseBase64 = pdfToBase64(data)
            # Add the data:application/pdf;base64, to the base64 string
            file = parseBase64['pdf']
            # Save temporal pdf
            fileName = f'resumen-de-negociacion-{gen_uuid()}.pdf'
            xmlData = b64decode(file, validate=True)
            with open(fileName, 'wb') as f:
                f.write(xmlData)

            # Get the document from niyaraki
            downloadDocument = requests.get(signature['message']['url'])
            if downloadDocument.status_code == 200:
                route = f'orden-de-compra-{gen_uuid()}.pdf'
                with open(route, 'wb') as archivo:
                    archivo.write(downloadDocument.content)
            else:
                print(f"Error al descargar el archivo: {downloadDocument.status_code}")

            headers = {
                'Authorization':'opuD1A63bkjnYULV1gDieYG+9B/R4D1kcYrwCB/qLjo='
            }

            filesBody = [
                ('archivo', (f'ORDEN DE COMPRA OP {opId} - {investor.upper()}.pdf', open(route, 'rb'), 'application/pdf')),
                ('archivo', (f'RESUMEN DE NEGOCIACION OP {opId}.pdf', open(fileName, 'rb'), 'application/pdf'))
                ]

            dataBody = {
                'numeroOperacion':request.data['integrationCode']
            }
 
            requestUrl = f"https://fd-appservice-test.azurewebsites.net/api/v1/Negotiation/{request.data['integrationCode']}/IntegrateNegotiation"
            request = requests.post(requestUrl, files=filesBody, data=dataBody, headers=headers)
            
            # Delete the files
            os.remove(route)
            os.remove(fileName)


            if request.status_code != 200:
                IntegrationHistory.objects.create(
                id=gen_uuid(),
                integrationCode=request.data['integrationCode'],
                status='FAILED',
                message=request.json()['message'],
                response=request.json()
                )
            else:
            # save the integration history
                IntegrationHistory.objects.create(
                    id=gen_uuid(),
                    integrationCode=request.data['integrationCode'],
                    status='SUCCESS',
                    message=request.json()['message'],
                    response=request.json()
                )

            return response({'error': False, 'message': 'operación realizada con éxito'}, 200)
        except Exception as e:
            IntegrationHistory.objects.create(
                id=gen_uuid(),
                integrationCode=None,
                status='FAILED',
                message=str(e),
                response=None
            )
            return response({'error': True, 'message': e}, 500)
