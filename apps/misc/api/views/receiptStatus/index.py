# REST Framework imports
from rest_framework.decorators import APIView
# Models
from apps.misc.models import ReceiptStatus
# Serializers
from apps.misc.api.serializers.index import ReceiptStatusSerializer
# Utils
from apps.base.utils.index import response
# Decorators
from apps.base.decorators.index import checkRole


class ReceiptStatusAV(APIView):
    
        def get(self, request, pk=None):
            try:
                if pk:
                    receiptStatus   = ReceiptStatus.objects.get(pk=pk)
                    serializer      = ReceiptStatusSerializer(receiptStatus)
                    return response({'error': False, 'data': serializer.data}, 200)
                else:
                    receiptStatus   = ReceiptStatus.objects.filter(state=1).order_by('description')
                    serializer      = ReceiptStatusSerializer(receiptStatus, many=True)
                    return response({'error': False, 'data': serializer.data}, 200)
            except ReceiptStatus.DoesNotExist:
                return response({'error': True, 'message': 'Estado de recaudo no encontrado'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
        @checkRole(['superuser'])
        def post(self, request):
            try:
                serializer = ReceiptStatusSerializer(data=request.data, context={'request':request})
                if serializer.is_valid():
                    serializer.save()
                    return response({'error': False, 'message': 'Estado de recaudo creado', 'data': serializer.data}, 200)
                return response({'error': True, 'message': serializer.errors}, 400)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
        @checkRole(['superuser'])
        def patch(self, request, pk):
            try:
                receiptStatus = ReceiptStatus.objects.get(pk=pk)
                serializer  = ReceiptStatusSerializer(receiptStatus, data=request.data, context={'request':request})
                if serializer.is_valid():
                    serializer.save()
                    return response({'error': False, 'message': 'Estado de recaudo actualizado', 'data':serializer.data}, 200)
                return response({'error': True, 'message': serializer.errors}, 400)
            except ReceiptStatus.DoesNotExist:
                return response({'error': True, 'message': 'Estado de recaudo no encontrado'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
        
        @checkRole(['superuser'])
        def delete(self, request, pk):
            try:
                ReceiptStatus = ReceiptStatus.objects.get(pk=pk)
                ReceiptStatus.state = 0
                ReceiptStatus.save()
                return response({'error': False, 'message': 'Estado de recaudo eliminado'}, 204)
            except ReceiptStatus.DoesNotExist:
                return response({'error': True, 'message': 'Estado de recaudo no encontrado'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)