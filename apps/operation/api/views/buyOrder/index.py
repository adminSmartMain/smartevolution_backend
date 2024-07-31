# Models
from apps.operation.models import BuyOrder, PreOperation
# Serializers
from apps.operation.api.serializers.index import BuyOrderSerializer, BuyOrderReadOnlySerializer
# Models 
from apps.report.api.models.index import NegotiationSummary
from apps.operation.api.models.index import PreOperation, BuyOrder, IntegrationHistory
from apps.administration.models import EmitterDeposit
from apps.client.models import LegalRepresentative
from apps.report.models import NegotiationSummary, PendingAccount
# Serializers
from apps.operation.api.serializers.preOperation.index import PreOperationReadOnlySerializer
# Utils
from apps.base.utils.index import response, BaseAV, gen_uuid, pdfToBase64
from apps.report.utils.electronicSignatureAPI import genElectronicSignature
from apps.report.utils.index import generateSellOfferByInvestor
from django.template.loader import get_template
import requests
from django.utils import timezone
from apps.report.utils.index import getSignatureStatus
from base64 import b64decode
import environ
import os
from collections import defaultdict

# Decorators
from apps.base.decorators.index import checkRole

class BuyOrderAV(BaseAV):
    
    @checkRole(['admin'])
    def post(self, request, pk=None):
        try:
            # Check if an negotiation summary exists for this operation
            negotiationSummary = NegotiationSummary.objects.filter(opId=request.data['opId']).first()
            if not negotiationSummary:
                return response({'error': True, 'message': 'No existe un resumen de negociación para esta operación'}, 400)
            #Get the operation
            operation = PreOperation.objects.filter(opId=request.data['opId'], investor=request.data['investorId']).first()
            requestId = f'ORDEN DE COMPRA OP {operation.opId} {operation.investor.first_name if operation.investor.first_name else operation.investor.social_reason}'
            sellOffer = generateSellOfferByInvestor(operation.opId,operation.investor.id)
            # gen the report
            template       = get_template('newBuyOrderSignatureTemplate.html')
            parsedTemplate = template.render(sellOffer)
            pdf            = pdfToBase64(parsedTemplate)
            
            # gen the electronic signature
            electronicSignature = genElectronicSignature(pdf, requestId, 'Orden de compra', requestId, [
            {
                'name' : sellOffer['legalRepresentative'],
                'email': sellOffer['legalRepresentativeEmail'],
                'phone': sellOffer['legalRepresentativePhone'],
                'label': True
            },])

            if electronicSignature['error'] == True:
                return response({'error': True, 'message': electronicSignature['message']['message']}, 400)
            buyOrderData = {
                'operation' : operation.id,
                'code'      : electronicSignature['message']['document'],
                'name'      : requestId,
                'url'       : '',
                'date'      : timezone.now().date().isoformat(),
                'status'    : 1,
                'signStatus': 0,
            }

            # serializer the buy order
            serializer = BuyOrderSerializer(data=buyOrderData, context={'request': request})
            if serializer.is_valid():
                serializer.save()
            else:
                return response({'error': True, 'message': serializer.errors}, 400)
            
            return response({'error': False, 'message':'Firma enviada correctamente'}, 200)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    

    @checkRole(['admin'])
    def get(self, request, pk=None):
        try:

            if len(request.query_params) > 0:
                if request.query_params.get('opId') != 'undefined':
                    buyOrder = BuyOrder.objects.get(operation__opId=request.query_params.get('opId'))
                    if buyOrder.signStatus != 1:
                        body = {
                            "request": "GET_SIGNATURE_STATUS",
                            "signature_id": buyOrder.idSignature,
                            "user": "smartevolution@co",
                            "password": "brtSji0_nQ",
                        }
                        res = requests.post('https://api.lleida.net/cs/v1/get_signature_status', json=body)
                        match res.json()['signature_status']:
                            case 'ready':
                                pass
                            case 'signed':
                                buyOrder.signStatus = 1
                                buyOrder.save()
                            case 'expired':
                                buyOrder.signStatus = 2
                                buyOrder.save()
                            case 'declined':
                                buyOrder.signStatus = 3
                                buyOrder.save()
                            case 'failed':
                                buyOrder.signStatus = 4
                                buyOrder.save()
                            case 'canceled':
                                buyOrder.signStatus = 5
                                buyOrder.save()

                    buyOrder = BuyOrder.objects.filter(operation__opId=request.query_params.get('opId'))
                    page       = self.paginate_queryset(buyOrder)
                    if page is not None:
                        serializer = BuyOrderReadOnlySerializer(page, many=True)
                        return self.get_paginated_response(serializer.data)                    
                else:
                    verifyBuyOrder   = BuyOrder.objects.all()
                    for x in verifyBuyOrder:
                        if x.signStatus != 1:
                            body = {
                                "request": "GET_SIGNATURE_STATUS",
                                "signature_id": x.idSignature,
                                "user": "smartevolution@co",
                                "password": "brtSji0_nQ",
                            }
                            # get the signature status
                            res = requests.post('https://api.lleida.net/cs/v1/get_signature_status', json=body)
                            match res.json()['signature_status']:
                                case 'ready':
                                    pass
                                case 'signed':
                                    #get all operations with the same opId
                                    operations = PreOperation.objects.filter(opId=x.operation.opId)
                                    # set the status of all operations to 3
                                    for operation in operations:
                                        operation.status = 3
                                        operation.save()
                                    x.signStatus = 1
                                    x.save()
                                case 'expired':
                                    #get all operations with the same opId
                                    operations = PreOperation.objects.filter(opId=x.operation.opId)
                                    # set the status of all operations to 3
                                    for operation in operations:
                                        operation.status = 5
                                        operation.save()
                                    x.signStatus = 2
                                    x.save()
                                case 'declined':
                                    x.signStatus = 3
                                    x.save()
                                case 'failed':
                                    x.signStatus = 4
                                    x.save()
                                case 'canceled':
                                    x.signStatus = 5
                                    x.save()
                                    
                    buyOrders  = BuyOrder.objects.all()
                    page       = self.paginate_queryset(buyOrders)
                    if page is not None:
                        serializer = BuyOrderReadOnlySerializer(page, many=True)
                        return self.get_paginated_response(serializer.data)


            if pk:
                if pk != 'all':
                    buyOrder   = BuyOrder.objects.get(pk=pk).first()
                    serializer = BuyOrderSerializer(buyOrder, context={'request': request})
                    return response({'error': False, 'data': serializer.data}, 200)
                else:
                    verifyBuyOrder   = BuyOrder.objects.all()
                    for x in verifyBuyOrder:
                        if x.signStatus != 1:
                            body = {
                                "request": "GET_SIGNATURE_STATUS",
                                "signature_id": x.idSignature,
                                "user": "smartevolution@co",
                                "password": "brtSji0_nQ",
                            }
                            # get the signature status
                            res = requests.post('https://api.lleida.net/cs/v1/get_signature_status', json=body)
                            match res.json()['signature_status']:
                                case 'ready':
                                    pass
                                case 'signed':
                                    if x.operation.status != 4:
                                        x.operation.status = 3
                                        x.operation.save()
                                    x.signStatus = 1
                                    x.save()
                                case 'expired':
                                    x.operation.status = 5
                                    x.operation.save()
                                    x.signStatus = 2
                                    x.save()
                                case 'declined':
                                    x.signStatus = 3
                                    x.save()
                                case 'failed':
                                    x.signStatus = 4
                                    x.save()
                                case 'canceled':
                                    x.signStatus = 5
                                    x.save()
                                    
                    buyOrders  = BuyOrder.objects.all()
                    page       = self.paginate_queryset(buyOrders)
                    if page is not None:
                        serializer = BuyOrderReadOnlySerializer(page, many=True)
                        return self.get_paginated_response(serializer.data)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
        


class BuyOrderWebhookAV(BaseAV):
    
    def post(self, request):
        try:
            environ.Env.read_env()
            env = environ.Env()
            if request.data['status'] == 'FINISH':
                # get the buy order from the document code
                buyOrder = BuyOrder.objects.get(code=request.data['code'])
                opId = buyOrder.operation.opId
                integrationCode = buyOrder.operation.bill.integrationCode
                buyOrder.signStatus = 1
                buyOrder.save()

                # get the operations with the same opId and the same investor then update the status to 1
                operations = PreOperation.objects.filter(opId=buyOrder.operation.opId, investor=buyOrder.operation.investor)

                for operation in operations:
                    operation.status = 1
                    operation.clientAccount.balance -= (operation.presentValueInvestor + operation.GM)
                    operation.clientAccount.save()
                    operation.save()

                # get the investors from the operation 
                investors = PreOperation.objects.filter(opId=buyOrder.operation.opId).values('investor').distinct()
                
                allBuyOrdersSent = False
                buyOrders        = []

                # check if every investor has a buy order
                for investor in investors:
                    if not BuyOrder.objects.filter(operation__opId=buyOrder.operation.opId, operation__investor=investor['investor']).exists():
                        allBuyOrdersSent = False
                        break
                    else:
                        allBuyOrdersSent = True
                        buyOrders.append(BuyOrder.objects.get(operation__opId=buyOrder.operation.opId, operation__investor=investor['investor']))

                if allBuyOrdersSent == False:
                    return response({'error': False, 'message': 'ok'}, 200)

                buyOrdersSigned = False
                buyOrderCodes   = []

                # check if all the buy orders are signed - status 1
                for buyOrder in buyOrders:
                    if buyOrder.signStatus != 1:
                        buyOrdersSigned = False
                        break
                    else:
                        buyOrdersSigned = True
                        buyOrderCodes.append(buyOrder.code)
                
                if buyOrdersSigned == False:
                    return response({'error': False, 'message': 'ok - buy order'}, 200)
                
                ordersSigned = False
                ordersUrl    = []

                for buyOrderCode in buyOrderCodes:
                    # Download the buy order
                    signature = getSignatureStatus(buyOrderCode)
                    if signature['message']['status'] == 'FINISH':
                        ordersSigned = True
                        # get the buy order from the document code
                        buyOrderData = BuyOrder.objects.get(code=buyOrderCode)
                        downloadDocument = requests.get(signature['message']['url'])
                        if downloadDocument.status_code == 200:
                            route = f'orden-de-compra-{gen_uuid()}.pdf'
                            with open(route, 'wb') as archivo:
                                archivo.write(downloadDocument.content)
                                ordersUrl.append({
                                    'route': route,
                                    'investor':buyOrderData.operation.investor.first_name if buyOrderData.operation.investor.first_name else buyOrderData.operation.investor.social_reason
                                })
                        else:
                                IntegrationHistory.objects.create(
                                    id=gen_uuid(),
                                    integrationCode=None,
                                    status='FAILED',
                                    message=f"Error al descargar el archivo: {downloadDocument.status_code}",
                                    response=None
                                )
                                return response({'error': True, 'message': f"Error al descargar el archivo: {downloadDocument.status_code}"}, downloadDocument.status_code)
                    else:
                        ordersSigned = False
                        break

                if ordersSigned == False:
                    # remove the files
                    for order in ordersUrl:
                        os.remove(order['route'])
                    return response({'error': False, 'message': 'ok'}, 200)
                

                # Gen the negotiation summary
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
                    'opId': buyOrder.operation.opId,
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
                fileName = f'resumen-de-negociacion-{gen_uuid()}.pdf'
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


                filesBody = []
                # generate the negotiation summary pdf
                template = get_template('negotiationSummary.html')
                renderedTemplate = template.render(data)
                parseBase64 = pdfToBase64(renderedTemplate)

                # Add the data:application/pdf;base64, to the base64 string
                file = parseBase64['pdf']
                # Save temporal pdf                        
                xmlData = b64decode(file, validate=True)
                with open(fileName, 'wb') as f:
                    f.write(xmlData)

                # add the negotiation summary to filesBody
                filesBody.append(('archivo', (f'RESUMEN DE NEGOCIACION OP {opId}.pdf', open(fileName, 'rb'), 'application/pdf')))
                for order in ordersUrl:
                    filesBody.append(('archivo', (f'ORDEN DE COMPRA OP {opId} {order["investor"]}.pdf', open(order['route'], 'rb'), 'application/pdf')))

                # send the request
                Headers = {
                    "Authorization":"LaKhDHjvVsmHuS/BNXfOdk1b8Y2w4fmNcDBUGtAnFnSlMieWJWvgcVHOJbgTORTJHeIXy3RgHCXEUVHGJf4cVA="
                }
                url = f"https://factoringdigital.azurewebsites.net/api/v1/Negotiation/{integrationCode}/IntegrateNegotiation"
                res = requests.post(url, data={"NumeroOperacion":opId}, files=filesBody, headers=Headers)
                
                if res.status_code != 200:
                    IntegrationHistory.objects.create(
                        id=gen_uuid(),
                        integrationCode=integrationCode,
                        status='FAILED',
                        message="",
                        response=res.json()
                        )
                else:
                    # save the integration history
                    IntegrationHistory.objects.create(
                        id=gen_uuid(),
                        integrationCode=integrationCode,
                        status='SUCCESS',
                        message="",
                        response=res.json()
                    )
                # delete the files
                os.remove(fileName)
                for order in ordersUrl:
                    os.remove(order['route'])
                return response({'error': False, 'message': 'ok'}, 200)
        except Exception as e:
            IntegrationHistory.objects.create(
            id=gen_uuid(),
            integrationCode=None,
            status='FAILED',
            message=str(e),
            response=None
            )
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)