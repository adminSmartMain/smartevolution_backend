# REST Framework imports
from rest_framework.decorators import APIView
# Models
from apps.misc.models import TypeReceipt
# Serializers
from apps.misc.api.serializers.index import TypeReceiptSerializer
# Utils
from apps.base.utils.index import response
# Decorators
from apps.base.decorators.index import checkRole


class TypeReceiptAV(APIView):
    
        def get(self, request, pk=None):
            try:
                if pk:
                    typeReceipt  = TypeReceipt.objects.get(pk=pk)
                    serializer   = TypeReceiptSerializer(typeReceipt)
                    return response({'error': False, 'data': serializer.data}, 200)
                else:
                    typeReceipt = TypeReceipt.objects.filter(state=1).order_by('description')
                    serializer    = TypeReceiptSerializer(typeReceipt, many=True)
                    return response({'error': False, 'data': serializer.data}, 200)
            except TypeReceipt.DoesNotExist:
                return response({'error': True, 'message': 'Tipo de recaudo no encontrado'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
        @checkRole(['superuser'])
        def post(self, request):
            try:
                serializer = TypeReceiptSerializer(data=request.data, context={'request':request})
                if serializer.is_valid():
                    serializer.save()
                    return response({'error': False, 'message': 'Tipo de recaudo creado', 'data': serializer.data}, 200)
                return response({'error': True, 'message': serializer.errors}, 400)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
        @checkRole(['superuser'])
        def patch(self, request, pk):
            try:
                typeReceipt = TypeReceipt.objects.get(pk=pk)
                serializer  = TypeReceiptSerializer(typeReceipt, data=request.data, context={'request':request})
                if serializer.is_valid():
                    serializer.save()
                    return response({'error': False, 'message': 'tipo de recaudo actualizado', 'data':serializer.data}, 200)
                return response({'error': True, 'message': serializer.errors}, 400)
            except TypeReceipt.DoesNotExist:
                return response({'error': True, 'message': 'Tipo de recaudo no encontrado'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
        
        @checkRole(['superuser'])
        def delete(self, request, pk):
            try:
                typeReceipt = TypeReceipt.objects.get(pk=pk)
                typeReceipt.state = 0
                typeReceipt.save()
                return response({'error': False, 'message': 'Tipo de recaudo eliminado'}, 204)
            except TypeReceipt.DoesNotExist:
                return response({'error': True, 'message': 'Tipo de recaudo no encontrado'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)