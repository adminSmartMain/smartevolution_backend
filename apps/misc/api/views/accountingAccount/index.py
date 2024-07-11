# REST Framework imports
from rest_framework.decorators import APIView
# Models
from apps.misc.models import AccountingAccount
# Serializers
from apps.misc.api.serializers.index import AccountingAccountSerializer
# Utils
from apps.base.utils.index import response
# Decorators
from apps.base.decorators.index import checkRole


class AccountingAccountAV(APIView):

    def get(self, request, pk=None):
            try:
                if pk != 'all' :
                    account    = AccountingAccount.objects.get(pk=pk)
                    serializer = AccountingAccountSerializer(account)
                    return response({'error': False, 'data': serializer.data}, 200)
                elif pk == 'all':
                    account    = AccountingAccount.objects.all()
                    serializer = AccountingAccountSerializer(account, many=True)
                    return response({'error': False, 'data': serializer.data}, 200)
                else:
                    activities = AccountingAccount.objects.filter(state=1).order_by('description')
                    serializer = AccountingAccountSerializer(activities, many=True)
                    return response({'error': False, 'data': serializer.data}, 200)
            except AccountingAccount.DoesNotExist:
                return response({'error': True, 'message': 'Cuenta no encontrada'}, 500)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['superuser'])
    def post(self, request):
            try:
                serializer = AccountingAccountSerializer(data=request.data, context={'request': request})
                if serializer.is_valid():
                    serializer.save()
                    return response({'error': False, 'message': 'Cuenta creada','data': serializer.data}, 200)
                return response({'error': True, 'message': serializer.errors}, 400)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['superuser'])
    def patch(self, request, pk):
            try:
                account    = AccountingAccount.objects.get(pk=pk)
                serializer = AccountingAccountSerializer(account, data=request.data, context={'request': request})
                if serializer.is_valid():
                    serializer.save()
                    return response({'error': False, 'message': 'Cuenta actualizada', 'data': serializer.data}, 200)
                return response({'error': True, 'message': serializer.errors}, 400)
            except AccountingAccount.DoesNotExist:
                return response({'error': True, 'message': 'Cuenta no encontrada'}, 500)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['superuser'])
    def delete(self, request, pk):
            try:
                account = AccountingAccount.objects.get(pk=pk)
                account.state = 0
                account.save()
                return response({'error': False, 'message': 'Cuenta eliminada'}, 204)
            except AccountingAccount.DoesNotExist:
                return response({'error': True, 'message': 'Cuenta no encontrada'}, 500)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
