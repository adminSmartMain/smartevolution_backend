# REST Framework imports
from rest_framework.decorators import APIView
# Models
from apps.misc.models import Bank
# Serializers
from apps.misc.api.serializers.index import BankSerializer
# Utils
from apps.base.utils.index import response
# Decorators
from apps.base.decorators.index import checkRole


class BankAV(APIView):
    
        def get(self, request, pk=None):
            try:
                if pk:
                    bank       = Bank.objects.get(pk=pk)
                    serializer = BankSerializer(bank)
                    return response({'error': False, 'data': serializer.data}, 200)
                else:
                    banks      = Bank.objects.filter(state=1).order_by('description')
                    serializer = BankSerializer(banks, many=True)
                    return response({'error': False, 'data': serializer.data}, 200)
            except Bank.DoesNotExist:
                return response({'error': True, 'message': 'banco no encontrado'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
        @checkRole(['superuser'])
        def post(self, request):
            try:
                serializer = BankSerializer(data=request.data, context={'request':request})
                if serializer.is_valid():
                    serializer.save()
                    return response({'error': False, 'message': 'banco creado', 'data':serializer.data}, 200)
                return response({'error': True, 'message': serializer.errors}, 400)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
        @checkRole(['superuser'])
        def patch(self, request, pk):
            try:
                bank       = Bank.objects.get(pk=pk)
                serializer = BankSerializer(bank, data=request.data, context={'request':request})
                if serializer.is_valid():
                    serializer.save()
                    return response({'error': False, 'message': 'banco actualizado', 'data':serializer.data}, 200)
                return response({'error': True, 'message': serializer.errors}, 400)
            except Bank.DoesNotExist:
                return response({'error': True, 'message': 'banco no encontrado'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
        
        @checkRole(['superuser'])
        def delete(self, request, pk):
            try:
                bank = Bank.objects.get(pk=pk)
                bank.state = 0
                bank.save()
                return response({'error': False, 'message': 'banco eliminado'}, 204)
            except Bank.DoesNotExist:
                return response({'error': True, 'message': 'banco no encontrado'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)