from django.db.models import Q

# Models
from apps.client.models import (LegalClient, ManagementBoard, PartnersAndShareholders,
                                 PrincipalProducts, PrincipalClients, PrincipalProviders,
                                 PrincipalCompetitors, FinancialRelations, LegalClientContacts,
                                 NaturalClient)
# Serializers
from apps.client.api.serializers.index import (LegalCLientSerializer, LegalClientReadOnlySerializer,NaturalClientSerializer, 
                                               NaturalClientReadOnlySerializer, LegalClientDocumentsSerializer, NaturalClientDocumentsSerializer)
# Utils
from apps.base.utils.index import response, BaseAV, gen_uuid, pdfToBase64, sendEmailWithTemplate
from django.template.loader import get_template
import requests
from datetime import datetime as dt
from django.utils import timezone
# Decorators 
from apps.base.decorators.index import checkRole


class LegalClientAV(BaseAV):

    def post(self, request):
        try:
            if len(request.query_params) > 0:
                # get the legal client data
                legalClient = LegalClient.objects.get(id=request.query_params.get('id'))
                # serialize the data
                serializer = LegalClientReadOnlySerializer(legalClient)
                template      = get_template('legalClient.html')
                parseTemplate = template.render(serializer.data)
                base64=pdfToBase64(parseTemplate)
                pdf = base64['pdf']
                messages = [f""<"Estimado/a {legalClient.companyName},\n\nMe gustaría recordarte que, por razones legales, es necesario que firmes electrónicamente el documento que te hemos enviado. La firma electrónica es un método seguro y legalmente reconocido para validar documentos y garantizar la autenticidad y la integridad de la información. Además, la firma electrónica ofrece una serie de ventajas, como la rapidez y la comodidad de firmar desde cualquier lugar en cualquier momento.\n\nSi tienes alguna duda o pregunta sobre el proceso de firma electrónica, no dudes en ponerte en contacto con nosotros. Estaremos encantados de ayudarte.\n\nAtentamente,\n\nSmart Evolution"""]
                # generate the electronic signature
                requestId = f'{legalClient.companyName} - FIRMA ELECTRONICA'
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
                                    "phone": "+" + legalClient.legalRepresentativePhone,
                                    "email": legalClient.legalRepresentativeEmail,
                                    "name" : legalClient.companyName,
                                    "position_id": "1"
                                }
                            ]
                        }
                    ],
                    "file": [
                        {
                            "filename": f"{requestId}.pdf",
                            "content": str(pdf),
                            'sign_on_landing': 'Y'
                        }
                    ]
                }
            }
                res = requests.post('https://api.lleida.net/cs/v1/start_signature', json=body)
                # save the signature
                url = res.json()['signature']['signatories'][0]['url']
                data = {
                'legalClient': legalClient.id,
                'url'        : url,
                'date'       : timezone.now().date().isoformat(),
                'idRequest'  : res.json()['request_id'],
                'idSignature': res.json()['signature']['signature_id'],
                'status'     : 0,
                'signStatus' : 0,
                }
                serializer = LegalClientDocumentsSerializer(data=data)
                if serializer.is_valid():
                    serializer.save()
                    # send the message
                    #sendWhatsApp(messages[0], legalClient.legalRepresentativePhone)
                    #sendWhatsApp(f'Link del documento a firmar {url}', legalClient.legalRepresentativePhone)
                    data = {
                        'description':legalClient.companyName,
                        'url': url,
                        'nit': legalClient.nit,
                        'typeVinculation': legalClient.typeVinculation,
                        'date':legalClient.created_at,
                        'email':legalClient.email,
                    }
                    sendEmailWithTemplate('Firma Electronica','legalClientRegister.html', data, [legalClient.email])
                    return response({'error': False, 'message':"Firma enviada" }, 200)
                else:
                    return response({'error': True, 'message':serializer.errors}, 400)
            else:                    
                serializer = LegalCLientSerializer(data=request.data, context={'request':request})
                if serializer.is_valid():
                    serializer.save()
                    # legal client instance
                    legalClient = LegalClient.objects.get(id=serializer.data['id'])

                    # register the management board
                    managementBoard = list(map(lambda x: ManagementBoard(
                        id= gen_uuid(),
                        legalClient=legalClient,
                        name= x['name'],
                        type= x['type'],
                        user_created_at= None,
                    ), request.data['managementBoard']))
                    # save the management board
                    ManagementBoard.objects.bulk_create(managementBoard)

                    # register the partners and shareholders
                    partnersAndShareholders = list(map( lambda x: PartnersAndShareholders(
                        id= gen_uuid(),
                        legalClient=legalClient,
                        name= x['name'],
                        documentNumber= x['documentNumber'],
                        percentage= x['percentage'],
                        user_created_at= None,
                    ), request.data['partnersAndShareholders']))
                    # save the partners and shareholders
                    PartnersAndShareholders.objects.bulk_create(partnersAndShareholders)

                    # register the principal products
                    principalProducts = list(map( lambda x: PrincipalProducts(
                        id= gen_uuid(),
                        legalClient=legalClient,
                        name= x['name'],
                        percentage= x['percentage'],
                        user_created_at= None,
                    ), request.data['principalProducts']))
                    # save the principal products
                    PrincipalProducts.objects.bulk_create(principalProducts)


                    # register the principal clients
                    principalClients = list(map( lambda x: PrincipalClients(
                        id= gen_uuid(),
                        legalClient= legalClient,
                        name= x['name'],
                        deadline= x['deadline'],
                        salePercentage= x['salePercentage'],
                        contactName= x['contactName'],
                        phone= x['phone'],
                        user_created_at= None,
                    ), request.data['principalClients']))
                    # save the principal clients
                    PrincipalClients.objects.bulk_create(principalClients)

                    # register the principal providers
                    principalProviders = list(map( lambda x: PrincipalProviders(
                        id= gen_uuid(),
                        legalClient=legalClient,
                        name= x['name'],
                        deadline= x['deadline'],
                        salePercentage= x['salePercentage'],
                        contactName= x['contactName'],
                        phone= x['phone'],
                        user_created_at= None,
                    ), request.data['principalProviders']))
                    # save the principal providers
                    PrincipalProviders.objects.bulk_create(principalProviders)

                    # register the principalCompetitors
                    principalCompetitors = list(map( lambda x: PrincipalCompetitors(
                        id= gen_uuid(),
                        legalClient=legalClient,
                        name= x['name'],
                        percentage= x['percentage'],
                        user_created_at= None,
                    ), request.data['principalCompetitors']))
                    # save the principalCompetitors
                    PrincipalCompetitors.objects.bulk_create(principalCompetitors)

                    # register the financialRelations
                    financialRelations = list(map( lambda x: FinancialRelations(
                        id= gen_uuid(),
                        legalClient=legalClient,
                        name= x['name'],
                        amount= x['amount'],
                        deadline= x['deadline'],
                        tax= x['tax'],
                        user_created_at= None,
                    ), request.data['financialRelations']))
                    # save the financialRelations
                    FinancialRelations.objects.bulk_create(financialRelations)

                    # register the legalClientContacts
                    legalClientContacts = list(map( lambda x: LegalClientContacts(
                        id=gen_uuid(),
                        legalClient=legalClient,
                        name=x['name'],
                        area=x['area'],
                        position= x['position'],
                        phone= x['phone'],
                        email= x['email'],
                        user_created_at= None,
                    ), request.data['legalClientContacts']))
                    # save the legalClientContacts
                    LegalClientContacts.objects.bulk_create(legalClientContacts)

                    return response({'error': False, 'data': serializer.data}, 200)
                else:
                    return response({'error': True, 'message': serializer.errors}, 400)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, 400)

    def get(self, request, pk=None):
        try:
            if pk:
                legalClient = LegalClient.objects.get(id=pk)
                serializer = LegalClientReadOnlySerializer(legalClient)
                return response({'error': False, 'data': serializer.data}, 200)

            elif len(request.query_params) > 0:
                if request.query_params.get('name') != None:
                    legalClient = LegalClient.objects.filter(companyName__icontains=request.query_params.get('name'))
                elif request.query_params.get('id') != None:
                    # get the legal client data
                    legalClient = LegalClient.objects.get(id=request.query_params.get('id'))
                    # serialize the data
                    serializer = LegalClientReadOnlySerializer(legalClient)
                    template      = get_template('legalClient.html')
                    parseTemplate = template.render(serializer.data)
                    base64=pdfToBase64(parseTemplate)
                    return response({'error': False, 'data': base64['pdf'], 'dict':serializer.data}, 200)

            legalClient = LegalClient.objects.all()
            page = self.paginate_queryset(legalClient)
            if page is not None:
                serializer = LegalClientReadOnlySerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, 400)

    def patch(self, request, pk):
        try:
            legalClient = LegalClient.objects.get(id=pk)
            serializer = LegalCLientSerializer(legalClient, data=request.data, partial=True, context={'request':request})
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'data': serializer.data}, 200)
            else:
                return response({'error': True, 'message': serializer.errors}, 400)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, 400)

    def delete(self, request, pk):
        try:
            legalClient = LegalClient.objects.get(id=pk)
            legalClient.delete()
            return response({'error': False, 'message': 'Legal client deleted'}, 200)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, 400)


class NaturalClientAV(BaseAV):
    def post(self, request):
        try:
            if len(request.query_params) > 0:
                # get the natural client data
                naturalClient = NaturalClient.objects.get(id=request.query_params.get('id'))
                serializer    = NaturalClientReadOnlySerializer(naturalClient)
                template      = get_template('naturalClient.html')
                parseTemplate = template.render(serializer.data)
                base64        = pdfToBase64(parseTemplate)
                pdf = base64['pdf']
                fullName = f'{naturalClient.firstName} {naturalClient.lastName}'
                messages = [f"""Estimado/a {fullName},\n\nMe gustaría recordarte que, por razones legales, es necesario que firmes electrónicamente el documento que te hemos enviado. La firma electrónica es un método seguro y legalmente reconocido para validar documentos y garantizar la autenticidad y la integridad de la información. Además, la firma electrónica ofrece una serie de ventajas, como la rapidez y la comodidad de firmar desde cualquier lugar en cualquier momento.\n\nSi tienes alguna duda o pregunta sobre el proceso de firma electrónica, no dudes en ponerte en contacto con nosotros. Estaremos encantados de ayudarte.\n\nAtentamente,\n\nSmart Evolution"""]
                # generate the electronic signature
                requestId = f'{fullName} - FIRMA ELECTRONICA'
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
                                    "phone": "+" + naturalClient.phone,
                                    "email": naturalClient.email,
                                    "name" : fullName,
                                    "position_id": "1"
                                }
                            ]
                        }
                    ],
                    "file": [
                        {
                            "filename": f"{requestId}.pdf",
                            "content": str(pdf),
                            'sign_on_landing': 'Y'
                        }
                    ]
                }
            }
                res = requests.post('https://api.lleida.net/cs/v1/start_signature', json=body)
                # save the signature
                url = res.json()['signature']['signatories'][0]['url']
                data = {
                'naturalClient': naturalClient.id,
                'url'          : url,
                'date'         : timezone.now().date().isoformat(),
                'idRequest'    : res.json()['request_id'],
                'idSignature'  : res.json()['signature']['signature_id'],
                'status'       : 0,
                'signStatus'   : 0,
                }
                serializer = NaturalClientDocumentsSerializer(data=data)
                if serializer.is_valid():
                    serializer.save()
                    # send the message
                    #sendWhatsApp(messages[0], naturalClient.phone)
                    #sendWhatsApp(f'Link del documento a firmar {url}', naturalClient.phone)
                    data = {
                        'description':naturalClient.firstName + ' ' + naturalClient.lastName,
                        'url': url,
                        'document': naturalClient.documentNumber ,
                        'typeVinculation': naturalClient.typeVinculation,
                        'date':naturalClient.created_at,
                        'email':naturalClient.email,
                    }
                    sendEmailWithTemplate('Firma Electronica','naturalClientRegister.html', data, [naturalClient.email])
                    return response({'error': False, 'message':"Firma enviada" }, 200)
                else:
                    return response({'error': True, 'message':serializer.errors}, 400)
            else:
                serializer = NaturalClientSerializer(data=request.data, context={'request':request})
                if serializer.is_valid():
                    serializer.save()
                    return response({'error': False, 'data': serializer.data}, 200)
                else:
                    return response({'error': True, 'message': serializer.errors}, 400)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, 400)

    def get(self, request, pk=None):
        try:
            if pk:
                naturalClient = NaturalClient.objects.get(id=pk)
                serializer = NaturalClientReadOnlySerializer(naturalClient)
                return response({'error': False, 'data': serializer.data}, 200)
            
            elif len(request.query_params) > 0:
                if request.query_params.get('id') != None:
                    # get the legal client data
                    naturalClient = NaturalClient.objects.get(id=request.query_params.get('id'))
                    # serialize the data
                    serializer = NaturalClientReadOnlySerializer(naturalClient)
                    template      = get_template('naturalClient.html')
                    parseTemplate = template.render(serializer.data)
                    base64= pdfToBase64(parseTemplate)
                    return response({'error': False, 'data': base64['pdf'], 'dict':serializer.data}, 200)
                elif request.query_params.get('name') != None:
                    naturalClient = NaturalClient.objects.filter(Q(first_name__icontains=request.query_params.get('name')) | Q(last_name__icontains=request.query_params.get('name')))
                    page = self.paginate_queryset(naturalClient)
                    if page is not None:
                        serializer = NaturalClientReadOnlySerializer(page, many=True)
                        return self.get_paginated_response(serializer.data)
            
            naturalClient = NaturalClient.objects.all()
            page = self.paginate_queryset(naturalClient)
            if page is not None:
                serializer = NaturalClientReadOnlySerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
                
        except Exception as e:
            return response({'error': True, 'message': str(e)}, 400)

    def patch(self, request, pk):
        try:
            naturalClient = NaturalClient.objects.get(id=pk)
            serializer = NaturalClientSerializer(naturalClient, data=request.data, partial=True, context={'request':request})
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'data': serializer.data}, 200)
            else:
                return response({'error': True, 'message': serializer.errors}, 400)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, 400)

    def delete(self, request, pk):
        try:
            naturalClient = NaturalClient.objects.get(id=pk)
            naturalClient.delete()
            return response({'error': False, 'message': 'Natural client deleted'}, 200)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, 400)