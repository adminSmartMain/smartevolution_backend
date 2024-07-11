# Serializer
from apps.client.api.serializers.index import ContactSerializer
# utils
import json
# Exceptions
from apps.base.exceptions import HttpException

def saveContacts(request, client, user=None):
    try:
        if request.data['type_client'] != '26c885fc-2a53-4199-a6c1-7e4e92032696':
            if 'contacts' in request.data:
                for contact in request.data['contacts']:
                    # get the id of the client
                    contact['client'] = client['id']
                    # register the contact of the client
                    serializer = ContactSerializer(data=contact, context={'request': request})
                    if serializer.is_valid():
                        # save the contact
                        serializer.save()
                        return serializer.data
                    else:
                        errors = {}
                        for x in client.errors:
                            errors[f'{x}'] = str(client.errors[f'{x}'][0])
                        raise HttpException(400, errors)
        else:
            contact = {
                'client'       : client['id'],
                'first_name'   : request.data['first_name'],
                'last_name'    : request.data['last_name'],
                'phone_number' : request.data['phone_number'],
                'email'        : request.data['email'],
                'position'     : 'representante legal',
            }
            serializer = ContactSerializer(data=contact, context={'request':request})
            if serializer.is_valid():
                serializer.save()
                return serializer
            else:
                errors = {}
                for x in client.errors:
                    errors[f'{x}'] = str(client.errors[f'{x}'][0])
                raise HttpException(400, errors)
                
    except Exception as e:
        raise HttpException(500, str(e))
