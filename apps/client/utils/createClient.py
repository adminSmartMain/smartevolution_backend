# Serializer
from apps.client.api.serializers.index import ClientSerializer
# Exceptions
from apps.base.exceptions import HttpException


def createClient(request, user=None):
    try:
        # set the client Data
        request.data['entered_by'] = request.user.id
        # Create a new client
        client = ClientSerializer(data=request.data, context={'request':request})
        if client.is_valid():
            # Save the client
            client.save()
            return client.data
        else:
            errors = {}
            for x in client.errors:
                errors[f'{x}'] = str(client.errors[f'{x}'][0])
            raise HttpException(400, errors)
    except Exception as e:
        raise HttpException(500, str(e))