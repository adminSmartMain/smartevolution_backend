# REST Framework imports
from django.db.models import Q 
# Models
from apps.client.models import Client, Account
# Serializers
from apps.client.api.serializers.index import ClientSerializer, ClientReadOnlySerializer, ClientByIdSerializer,LegalRepresentativeSerializer, ContactSerializer
from apps.authentication.api.serializers.index import UserSerializer
# Utils
from apps.base.utils.index import response, BaseAV
from apps.client.utils.index import createClient, saveContacts, saveLegalRepresentative, createAccount, genRequest
# Decorators
from apps.base.decorators.index import checkRole


class ClientAV(BaseAV):
    @checkRole(['admin'])
    def get(self, request, pk=None):
        try:
            
            if len(request.query_params) > 0:
                if request.query_params.get('client') != None:
                    clients    = Client.objects.filter(Q(social_reason__icontains=request.query_params.get('client')) | Q(first_name__icontains=request.query_params.get('client')) | Q(last_name__icontains=request.query_params.get('client'))).filter(state=1)
                    page       = self.paginate_queryset(clients)
                    if page is not None:
                        serializer = ClientReadOnlySerializer(page, many=True)
                        return self.get_paginated_response(serializer.data)

                if request.query_params.get('document') != None:
                    clients    = Client.objects.filter(document_number__icontains=request.query_params.get('document')).filter(state=1)
                    page       = self.paginate_queryset(clients)
                    if page is not None:
                        serializer = ClientReadOnlySerializer(page, many=True)
                        return self.get_paginated_response(serializer.data)

            if pk:
                client     = Client.objects.get(id=pk) if pk != 'all' else Client.objects.filter(state=1)
                serializer = ClientByIdSerializer(client) if pk != 'all' else ClientSerializer(client, many=True)
                return response({'error': False, 'data': serializer.data}, 200)
            else:
                clients    = Client.objects.filter(state=1)
                page       = self.paginate_queryset(clients)
                if page is not None:
                    serializer = ClientReadOnlySerializer(page, many=True)
                    return self.get_paginated_response(serializer.data)
        except Client.DoesNotExist:
            return response({'error': True, 'message': 'Clientes no encontrados'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
    @checkRole(['admin'])
    def post(self, request):
        try:
            # check if the user already exists
            if request.data['type_client'] == 'e646e875-c07f-420e-90e5-cae468587c05':
                if Client.objects.filter(email=request.data['email']).exists():
                    return response({'error': True, 'message': 'Ya existe un usuario con este email'}, 400)
            # set the user of the new client as the user of the request
            getUser = None
            # set the user who registered this client
            request.data['entered_by'] = request.user.id
            # set the user of the new client
            request.data['user']       = getUser
            # Create a new client
            client = createClient(request, getUser)
            # Save the contacts
            saveContacts(request, client, getUser)
            # Save the legal representative of the client
            saveLegalRepresentative(request, client, getUser)
            # Create the account of the client
            createAccount(request, client, getUser)
            return response({'error': False, 'message': 'cliente registrado', 'data':client}, 201)
        except Exception as e:
            return response({'error': True, 'message': eval(e.detail)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['admin'])
    def patch(self, request, pk=None):
        try:
            client     = Client.objects.get(id=pk)
            serializer = ClientSerializer(client, data=request.data, partial=True, context={'request':request})
            if serializer.is_valid():
                serializer.save()
                if 'legal_representative' in request.data:
                    LegalRepresentative= LegalRepresentativeSerializer.Meta.model.objects.get(client=client)
                    lRSerializer = LegalRepresentativeSerializer(LegalRepresentative, data=request.data['legal_representative'], partial=True, context={'request':request})
                    if lRSerializer.is_valid():
                        lRSerializer.save()
                # validate if the client has contacts
                if 'contacts' in request.data:
                    # get the contacts of the client
                    contacts = ContactSerializer.Meta.model.objects.filter(client=client)
                    # validate if the client has contacts
                    if len(contacts) > 0:
                        # delete the contacts of the client
                        ContactSerializer.Meta.model.objects.filter(client=client).delete()
                    # save the new contacts
                    for x in request.data['contacts']:
                        x['client'] = client.id
                        contactSerializer = ContactSerializer(data=x, context={'request':request})
                        if contactSerializer.is_valid():
                            contactSerializer.save()
                    
                return response({'error': False, 'data': serializer.data}, 200)
            else:
                return response({'error': True, 'message': serializer.errors}, 400)
        except Client.DoesNotExist:
            return response({'error': True, 'message': 'Cliente no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['admin'])
    def delete(self, request, pk=None):
        try:
            client = Client.objects.get(id=pk)
            client.state = 0
            client.save()
            # disable the accounts of the client
            Account.objects.filter(client=client).update(state=0)
            return response({'error': False, 'message': 'Cliente eliminado'}, 200)
        except Client.DoesNotExist:
            return response({'error': True, 'message': 'Client no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)


class ClientByTermAV(BaseAV):
    @checkRole(['admin'])
    def get(self, request, term=None):
        try:
            clients = Client.objects.filter(Q(social_reason__icontains=term) | Q(first_name__icontains=term) | Q(last_name__icontains=term) | Q(document_number__icontains=term))
            serializer = ClientByIdSerializer(clients, many=True)
            return response({'error': False, 'data': serializer.data}, 200)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)


    @checkRole(['admin'])
    def get(self, request):
        try:
            if request.query_params.get('client') != None:
                clients = Client.objects.filter(Q(social_reason__icontains=request.query_params.get('client')) | Q(first_name__icontains=request.query_params.get('client')) | Q(last_name__icontains=request.query_params.get('client')))
                
            if request.query_params.get('document') != None:
                clients = Client.filter(document_number__icontains=request.query_params.get('document'))

            serializer = ClientSerializer(clients, many=True)
            return response({'error': False, 'data': serializer.data}, 200)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)