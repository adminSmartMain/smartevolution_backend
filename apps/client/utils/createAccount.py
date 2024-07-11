# Serializer
from apps.client.api.serializers.index import AccountSerializer
# Exceptions
from apps.base.exceptions import HttpException
# Utils
from apps.base.utils.index import random_with_N_digits

def createAccount(request, client, user= None):
    try:
        serializer = AccountSerializer(data={'client': client['id'], 'primary': True, 'account_number':random_with_N_digits(10)}, context={'request': request})
        if serializer.is_valid():
            # Save the account
            serializer.save()
            return serializer
        else:
            errors = {}
            for x in client.errors:
                errors[f'{x}'] = str(client.errors[f'{x}'][0])
            raise HttpException(400, errors)
    except Exception as e:
        raise HttpException(500, str(e))