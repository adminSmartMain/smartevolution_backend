# REST Framework imports
from rest_framework.decorators import APIView
# Models
from apps.misc.models import AccountType
# Serializers
from apps.misc.api.serializers.index import AccountTypeSerializer
# Utils
from apps.base.utils.index import response
# Decorators
from apps.base.decorators.index import checkRole


class AccountTypeAV(APIView):

    def get(self, request, pk=None):
        try:
            if pk:
                account_type = AccountType.objects.get(pk=pk)
                serializer   = AccountTypeSerializer(account_type)
                return response({'error': False, 'data': serializer.data}, 200)
            else:
                account_types = AccountType.objects.filter(state=1).order_by('description')
                serializer    = AccountTypeSerializer(account_types, many=True)
                return response({'error': False, 'data': serializer.data}, 200)
        except AccountType.DoesNotExist:
            return response({'error': True, 'message': 'tipo de cuenta no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['superuser'])
    def post(self, request):
        try:
            serializer = AccountTypeSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'message': 'tipo de cuenta creado', 'data': serializer.data}, 200)
            return response({'error': True, 'message': serializer.errors}, 400)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['superuser'])
    def patch(self, request, pk):
        try:
            account_type = AccountType.objects.get(pk=pk)
            serializer = AccountTypeSerializer(
                account_type, data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'message': 'tipo de cuenta actualizado', 'data': serializer.data}, 200)
            return response({'error': True, 'message': serializer.errors}, 400)
        except AccountType.DoesNotExist:
            return response({'error': True, 'message': 'tipo de cuenta no encontrado'}, 500)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['superuser'])
    def delete(self, request, pk):
        try:
            account_type = AccountType.objects.get(pk=pk)
            account_type.state = 0
            account_type.save()
            return response({'error': False, 'message': 'tipo de cuenta eliminado'}, 204)
        except AccountType.DoesNotExist:
            return response({'error': True, 'message': 'tipo de cuenta no encontrado'}, 500)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
