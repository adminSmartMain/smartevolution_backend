# Serializer
from apps.client.api.serializers.index import LegalRepresentativeSerializer
# utils
import json
# Exceptions
from apps.base.exceptions import HttpException

def saveLegalRepresentative(request, client, user=None):
    try:
        if request.data['type_client'] != '26c885fc-2a53-4199-a6c1-7e4e92032696':
            f           = request.data['legal_representative']
            f['client'] = client['id']
            serializer  = LegalRepresentativeSerializer(data=f, context={'request': request})
            if serializer.is_valid():
                # Save the legal representative
                serializer.save()
            else:
                errors = {}
                for x in client.errors:
                    errors[f'{x}'] = str(client.errors[f'{x}'][0])
                raise HttpException(400, errors)
        else:
            data = {
                'client': client['id'],
                'type_identity': request.data['type_identity'],
                'document_number': request.data['document_number'],
                'first_name': request.data['first_name'],
                'last_name': request.data['last_name'],
                'birth_date': None,
                'city': request.data['city'],
                'citizenship': request.data['citizenship'],
                'address': request.data['address'],
                'phone_number': request.data['phone_number'],
                'email': request.data['email'],
                'position': 'representante legal',
            }
            serializer = LegalRepresentativeSerializer(data=data, context={'request': request})
            if serializer.is_valid():
                # Save the legal representative
                serializer.save()
            else:
                errors = {}
                for x in client.errors:
                    errors[f'{x}'] = str(client.errors[f'{x}'][0])
                raise HttpException(400, errors)
            return True
    except Exception as e:
        raise HttpException(500, str(e))