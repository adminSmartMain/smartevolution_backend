from rest_framework.decorators import APIView
# Models
from apps.report.api.models.index import SellOrder, SellOrderOperation
from apps.operation.api.models.index import PreOperation
from apps.client.api.models.index import LegalRepresentative, Client
# Serializers
from apps.report.api.serializers.sellOrder.index       import SellOrderSerializer
from apps.operation.api.serializers.preOperation.index import PreOperationSerializer
from apps.operation.api.serializers.index import BuyOrderSerializer
# Utils
from apps.base.utils.index import response, sendWhatsApp, sendEmail, genVerificationCode, gen_uuid, html_to_pdf_base64, pdfToBase64
from django.template.loader import get_template
from apps.report.utils.index import generateSellOffer, generateSellOfferByInvestor
import requests
from django.utils import timezone
from twilio.twiml.messaging_response import Body, Message, Redirect, MessagingResponse
from rest_framework_xml.renderers import XMLRenderer
# Decorators
from apps.base.decorators.index import checkRole


class MessagesAV(APIView):
    
    @checkRole(['admin'])
    def post(self, request, *args, **kwargs):
        print("ACA")
        balance = request.data['balance']
        emitter = request.data['emitter']
        bills   = request.data['bills']
        averageTerm = request.data['averageTerm']
        amount = request.data['amount']
        investorName = ''
        #split the name of the investor if it has more than one name
        splitInvestorName = request.data['investor'].split(' ')
        match len(splitInvestorName):
            case 1:
                investorName = splitInvestorName[0]
            case 2:
                investorName = splitInvestorName[0] + ' ' + splitInvestorName[1]
            case 3:
                investorName = splitInvestorName[0] + ' ' + splitInvestorName[2]
            case 4:
                investorName = splitInvestorName[0] + ' ' + splitInvestorName[2]
        print("ACA2")
        
        requestOpId = request.data['opId']
        sellOffer = generateSellOfferByInvestor(request.data['opId'],request.data[''],'P-')
        #gen the report
        template = get_template('buyorder.html')
        parsedTemplate = template.render(sellOffer)
        approveCode = genVerificationCode()
        rejectCode  = genVerificationCode()
        # get the client
        client = Client.objects.get(id=request.data['investorId'])
        pdf = pdfToBase64(parsedTemplate)
        # save the report
        print("ACA3")
        
        serializer = SellOrderSerializer(data={ 'file'        : pdf['pdf'],
                                                'opId'        : request.data['opId'],
                                                'client'      : client.id,
                                                'approveCode' : approveCode,
                                                'rejectCode'  : rejectCode }, context={'request': request})
        if serializer.is_valid():
            serializer.save()
        else:
            return response({'error': True, 'message': serializer.errors}, 400)

        # Get the sell order
        sellOrder = SellOrder.objects.get(id=serializer.data['id'])

        # get the investor operations
        operations = PreOperation.objects.filter(investor=request.data['investorId'], opId=request.data['opId'])

        # save the operations in the sell order operations
        for x in operations:
            SellOrderOperation.objects.create(id=gen_uuid(), sellOrder=sellOrder, operation=x)

        # set the messages

        # get the payers names from the request and contact them
        payers = ''
        for x in request.data['payers']:
            #remove the . at the final of the name
            payers += x['name'][:-1]

        messages = [
            f'Estimado {investorName}.\nLe informamos que cuenta con un disponible de $ {"{:,}".format(round(balance))} COP. Por lo anterior, nos gustaría ofrecerle la \nsiguiente operación:\nEmisor: {emitter}\nPagador(es):{payers}\nCantidad de Facturas: {bills}\nPlazo Promedio: {averageTerm} días\nMonto: $ {"{:,}".format(amount)} COP\nA continuación le enviaremos la ficha técnica con los detalles de la operación para su consulta.',
            f'Si está de acuerdo con la operación, por favor responda {approveCode}. En caso contrario, por favor responda {rejectCode}.\nSi desea conversar con nosotros, por favor escriba su requerimiento y nos estaremos comunicando con usted a la brevedad. ¡Muchas gracias!',
        ]

        # get the legal representative of the investor
        legalRepresentative = LegalRepresentative.objects.get(client=request.data['investorId'])
        

        # send the notification message
        sendWhatsApp(f'Oferta de venta operacion Nro {requestOpId} - SMART EVOLUTION', legalRepresentative.phone_number)
        # send the fist message
        sendWhatsApp(messages[0], legalRepresentative.phone_number)
        # send the file
        sendWhatsApp(f'Ficha técnica de la operación {sellOrder.file.url}', legalRepresentative.phone_number)
        # send the second message
        sendWhatsApp(messages[1], legalRepresentative.phone_number)

        return response({'error': False, 'data': {
            'approveCode': approveCode,
            'rejectCode': rejectCode,
        }}, 200)
   
    def get(self, request):
        return response({'error': False, 'data': 'xd' }, 200)
    
class MessagesTestAV(APIView):
    
    @checkRole(['admin'])
    def post(self, request, *args, **kwargs):
        balance = request.data['balance']
        emitter = request.data['emitter']
        bills   = request.data['bills']
        averageTerm = request.data['averageTerm']
        amount = request.data['amount']
        investorName = ''
        #split the name of the investor if it has more than one name
        splitInvestorName = request.data['investor'].split(' ')
        match len(splitInvestorName):
            case 1:
                investorName = splitInvestorName[0]
            case 2:
                investorName = splitInvestorName[0] + ' ' + splitInvestorName[1]
            case 3:
                investorName = splitInvestorName[0] + ' ' + splitInvestorName[2]
            case 4:
                investorName = splitInvestorName[0] + ' ' + splitInvestorName[2]
        requestOpId = request.data['opId']
        sellOffer = generateSellOfferByInvestor(request.data['opId'],request.data['investorId'],'P-')
        #gen the report
        template = get_template('buyorder.html')
        parsedTemplate = template.render(sellOffer)
        approveCode = genVerificationCode()
        rejectCode  = genVerificationCode()
        # get the client
        client = Client.objects.get(id=request.data['investorId'])
        pdf = pdfToBase64(parsedTemplate)
        # save the report
        serializer = SellOrderSerializer(data={ 'file'        : pdf['pdf'],
                                                'opId'        : request.data['opId'],
                                                'client'      : client.id,
                                                'approveCode' : approveCode,
                                                'rejectCode'  : rejectCode }, context={'request': request})
        if serializer.is_valid():
            serializer.save()
        else:
            return response({'error': True, 'message': serializer.errors}, 400)

        # Get the sell order
        sellOrder = SellOrder.objects.get(id=serializer.data['id'])

        # get the investor operations
        operations = PreOperation.objects.filter(investor=request.data['investorId'], opId=request.data['opId'])

        # save the operations in the sell order operations
        for x in operations:
            SellOrderOperation.objects.create(id=gen_uuid(), sellOrder=sellOrder, operation=x)

        # set the messages

        # get the payers names from the request and contact them
        payers = ''
        for x in request.data['payers']:
            #remove the . at the final of the name
            payers += x['name'][:-1]

        messages = [
            f'Estimado {investorName}.\nLe informamos que cuenta con un disponible de $ {"{:,}".format(round(balance))} COP. Por lo anterior, nos gustaría ofrecerle la \nsiguiente operación:\nEmisor: {emitter}\nPagador(es):{payers}\nCantidad de Facturas: {bills}\nPlazo Promedio: {averageTerm} días\nMonto: $ {"{:,}".format(amount)} COP\nA continuación le enviaremos la ficha técnica con los detalles de la operación para su consulta.',
            f'Si está de acuerdo con la operación, por favor responda {approveCode}. En caso contrario, por favor responda {rejectCode}.\nSi desea conversar con nosotros, por favor escriba su requerimiento y nos estaremos comunicando con usted a la brevedad. ¡Muchas gracias!',
        ]

        # get the legal representative of the investor
        legalRepresentative = LegalRepresentative.objects.get(client=request.data['investorId'])
        

        # send the notification message
        sendWhatsApp(f'Oferta de venta operacion Nro {requestOpId} - SMART EVOLUTION', legalRepresentative.phone_number)
        # send the fist message
        sendWhatsApp(messages[0], legalRepresentative.phone_number)
        # send the file
        sendWhatsApp(f'Ficha técnica de la operación {sellOrder.file.url}', legalRepresentative.phone_number)
        # send the second message
        sendWhatsApp(messages[1], legalRepresentative.phone_number)

        return response({'error': False, 'data': {
            'approveCode': approveCode,
            'rejectCode': rejectCode,
        }}, 200)
    
    def get(self, request):
        return response({'error': False, 'data': 'xd' }, 200)
    
class SignatureAV(APIView):
    def post(self, request):
        try:
            investor = Client.objects.get(id=request.data['investorId'])
            # Get the investor
            # Get the legal representative
            legalRepresentative = LegalRepresentative.objects.get(client=investor.id)
            # Generate the sellOrder
            sellOffer = generateSellOfferByInvestor(request.data['opId'],request.data['investorId'],'')
            #gen the report
            template = get_template('buyorder.html')
            parsedTemplate = template.render(sellOffer)
            pdf  = pdfToBase64(parsedTemplate)
            # save the report
            serializer = SellOrderSerializer(data={ 'file'        : pdf['pdf'],
                                                    'opId'        : request.data['opId'],
                                                    'client'      : investor.id,
                                                    'approveCode' : 0,
                                                    'rejectCode'  : 0,
                                                    'status': 1 }, context={'request': request})
            if serializer.is_valid():
                serializer.save()
            else:
                return response({'error': True, 'message': serializer.errors}, 400)
            # Get the sell order
            sellOrder = SellOrder.objects.get(id=serializer.data['id'])
            # Gen the electronic signature
            operation = PreOperation.objects.filter(investor=investor.id, opId=sellOrder.opId).first()
            requestId = f'ORDEN DE COMPRA OP {operation.opId} {operation.investor.first_name if operation.investor.first_name else operation.investor.social_reason}'
            pdf = requests.post('https://j2ncm3xeo7.execute-api.us-east-1.amazonaws.com/dev/api/html-to-pdf', json={'html': test})
            body = {
                    "request": "START_SIGNATURE",
                    "request_id": requestId,
                    "user": "smartevolution@co",
                    "password": "brtSji0_nQ",
                    "signature": {
                        "config_id": 34962,
                        "contract_id": requestId,
                        "level": [
                            {
                                "level_order": 1,
                                "required_signatories_to_complete_level": 2,
                                "signatories": [
                                    {
                                        "phone": "+" + legalRepresentative.phone_number,
                                        "email": operation.investor.email,
                                        "name" : operation.investor.first_name + ' ' + operation.investor.last_name if operation.investor.first_name else operation.investor.social_reason,
                                        "position_id": "1"
                                    }
                                ]
                            }
                        ],
                        "file": [
                            {
                                "filename": f"{requestId}.pdf",
                                "content": str(pdf.json()['pdf']),
                                'sign_on_landing': 'Y'
                            }
                        ]
                    }
                }
            res = requests.post('https://api.lleida.net/cs/v1/start_signature', json=body)
            # save the signature
            buyOrder = {
                    'operation'  : operation.id,
                    'url'        : res.json()['signature']['signatories'][0]['url'],
                    'date'       : timezone.now().date().isoformat(),
                    'idRequest'  : res.json()['request_id'],
                    'idSignature': res.json()['signature']['signature_id'],
                    'status'     : 0,
                    'signStatus' : 0,
                }
            serializer = BuyOrderSerializer(data=buyOrder, context={'request': request})
            if serializer.is_valid():
                # delete the codes from the sell order
                serializer.save()
            else:
                return response({'error': True, 'message': serializer.errors}, 400)
            # send the notification message
            url = buyOrder['url']
            sendWhatsApp(f'Para completar el proceso de compra de la operación {operation.opId}, ingrese al siguiente link {url}.', legalRepresentative.phone_number)
            return response({'error': False, 'data': serializer.data, 'message':'Firma electronica enviada'}, 200)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, 500)





class TwilioMessageHandlerAV(APIView):

    def post(self, request, *args, **kwargs):
        try:
            # get the code from the message
            code = request.data['Body']
            # get the phone number from the message - whatsapp:+573186078741
            # remove the whatsapp: and the +
            phone = request.data['From'][10:]

            #get the sell order client
            legalRepresentative = LegalRepresentative.objects.get(phone_number=phone)
            client = legalRepresentative.client
            #check if the message is a number
            if code.isdigit():
                pass
            else:
                sendWhatsApp(f'mensage proveniente del cliente {client.first_name+" "+ client.last_name if client.first_name else client.social_reason} , {code}', '573244296262')
                return response({'error': False, 'message': 'message sent'}, 200)
            
            # get the sell order operations
            sellOrderOperations = SellOrderOperation.objects.filter(operation__investor=client.id)

            # get the sell order
            sellOrder = SellOrder.objects.get(id=sellOrderOperations[0].sellOrder.id, status = 0)

            # verify if the client is the owner of the sell order
            if sellOrder.client.id != client.id:
                sendWhatsApp('Codigo Invalido', phone)

            # check if the code is a approve or reject code
            if code == sellOrder.approveCode:
                clientName = client.first_name + ' ' + client.last_name if client.first_name else client.social_reason
                # get the investor operations
                operations = PreOperation.objects.filter(investor=client.id, opId=sellOrder.opId)
                # update the operations status
                for x in operations:
                    x.status = 1
                    #x.clientAccount.balance -= x.amount
                    #x.clientAccount.save()
                    x.save()
                sendWhatsApp(f'La operacion {sellOrder.opId} ha sido aprobada por el inversionista {clientName}.', '573244296262')
                # set the sell order status to approved and save it
                sellOrder.status = 1
                sellOrder.save()
                sendWhatsApp('Operacion Aprobada', phone)
                # generate the electronic signature
                operation = PreOperation.objects.filter(investor=client.id, opId=sellOrder.opId).first()
                requestId = f'ORDEN DE COMPRA OP {operation.opId} {operation.investor.first_name if operation.investor.first_name else operation.investor.social_reason}'
                sellOffer = generateSellOfferByInvestor(sellOrder.opId,client.id)
                # gen the report
                template = get_template('buyorder.html')
                parsedTemplate = template.render(sellOffer)
                pdf  = pdfToBase64(parsedTemplate)
                body = {
                "request": "START_SIGNATURE",
                "request_id": requestId,
                "user": "smartevolution@co",
                "password": "brtSji0_nQ",
                "signature": {
                    "config_id": 34962,
                    "contract_id": requestId,
                    "level": [
                        {
                            "level_order": 1,
                            "required_signatories_to_complete_level": 2,
                            "signatories": [
                                {
                                    "phone": "+" + legalRepresentative.phone_number,
                                    "email": operation.investor.email,
                                    "name" : operation.investor.first_name + ' ' + operation.investor.last_name if operation.investor.first_name else operation.investor.social_reason,
                                    "position_id": "1"
                                }
                            ]
                        }
                    ],
                    "file": [
                        {
                            "filename": f"{requestId}.pdf",
                            "content": str(pdf.json()['pdf']),
                            'sign_on_landing': 'Y'
                        }
                    ]
                }
            }
                res = requests.post('https://api.lleida.net/cs/v1/start_signature', json=body)
                # buyOrder data
                buyOrder = {
                'operation'  : operation.id,
                'url'        : res.json()['signature']['signatories'][0]['url'],
                'date'       : timezone.now().date().isoformat(),
                'idRequest'  : res.json()['request_id'],
                'idSignature': res.json()['signature']['signature_id'],
                'status'     : 0,
                'signStatus' : 0,
            }
                # save the buy order
                serializer = BuyOrderSerializer(data=buyOrder, context={'request': request})
                if serializer.is_valid():
                    # delete the codes from the sell order
                    sellOrder.approveCode = 0
                    sellOrder.rejectCode  = 0
                    sellOrder.save()
                    serializer.save()
                else:
                    return response({'error': True, 'message': serializer.errors}, 400)
                # get the legal representative of the client
                sendWhatsApp('Firma Electronica Generada', phone)
                sendWhatsApp(f'{buyOrder["url"]}', phone)
            elif code == sellOrder.rejectCode:
                clientName = client.first_name + ' ' + client.last_name if client.first_name else client.social_reason
                # get the investor operations
                operations = PreOperation.objects.filter(investor=client.id, opId=sellOrder.opId)
                # update the operations status
                for x in operations:
                    x.bill.currentBalance += x.payedAmount
                    #x.clientAccount.balance += (x.payedAmount + x.GM)
                    #x.clientAccount.save()
                    x.bill.save()
                    x.status = 2
                    x.save()
                sendWhatsApp(f'La operacion {sellOrder.opId} ha sido rechazada por el inversionista {clientName}.', '573244296262')
                # set the sell order status to reject and save it
                sellOrder.status = 1
                # delete the codes from the sell order
                sellOrder.approveCode = 0
                sellOrder.rejectCode  = 0
                sellOrder.save()
                sendWhatsApp('Operacion Rechazada', phone)
            else:
                #check if the message is a number
                if code.isdigit():
                    sendWhatsApp('Codigo Invalido', phone)
                else:
                    sendWhatsApp(f'mensage proveniente del cliente {client.first_name+" "+ client.last_name if client.first_name else client.social_reason} , {code}', '573244296262')


            # return twilio response

            # verify if the code is a approve or reject code
            if SellOrder.objects.filter(approveCode=code).exists():
                return response({'error': False, 'data': {'status' : 'operacion aprobada', 'phone':phone }}, 200)
            elif SellOrder.objects.filter(rejectCode=code).exists():
                return response({'error': False, 'data': {'status' : 'operacion rechazada', 'phone':phone }}, 200)
            else:
                return response({'error': False, 'data': {'status' : 'codigo invalido', 'phone':phone }}, 200)

        except Exception as e:
            return response({'error': True, 'message': str(e)}, 500)