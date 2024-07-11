# Serializer
from apps.client.api.serializers.index import RequestSerializer
# Exceptions
from apps.base.exceptions import HttpException

def genRequest(request, client, user=None):
    try:
        serializer = RequestSerializer(data={'client': client['id']}, context={'request':request})
        if serializer.is_valid():
            # Save the request
            serializer.save()
            return serializer
        else:
            errors = {}
            for x in client.errors:
                errors[f'{x}'] = str(client.errors[f'{x}'][0])
            raise HttpException(400, errors)
    except Exception as e:
        raise HttpException(500, str(e))