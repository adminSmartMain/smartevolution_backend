# REST Framework imports
from rest_framework.decorators import APIView
# Models
from apps.operation.models import Receipt
# Serializers
from apps.operation.api.serializers.index import ReceiptSerializer, ReceiptReadOnlySerializer
# Utils
from apps.base.utils.index import response, BaseAV
# Decorators
from apps.base.decorators.index import checkRole

class ReceiptAV(BaseAV):

    @checkRole(['admin'])
    def get(self, request, pk=None):
        try:
            
            if len(request.query_params) > 0:
                if request.query_params.get('opId') != '':
                    receipts    = Receipt.objects.filter(operation__opId=request.query_params.get('opId'))
                    page        = self.paginate_queryset(receipts)
                    if page is not None:
                        serializer = ReceiptReadOnlySerializer(page, many=True)
                        return self.get_paginated_response(serializer.data)
                else:
                    receipts    = Receipt.objects.filter(state=1)
                    page        = self.paginate_queryset(receipts)
                    if page is not None:
                        serializer = ReceiptReadOnlySerializer(page, many=True)
                        return self.get_paginated_response(serializer.data)


            if pk:
                receipt      = Receipt.objects.get(pk=pk)
                serializer   = ReceiptSerializer(receipt)
                return response({'error': False, 'data': serializer.data}, 200)
        except Receipt.DoesNotExist:
            return response({'error': True, 'message': 'recaudo/s no encontrados'}, 500)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['admin'])
    def post(self, request):
        try:
            serializer = ReceiptSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'message': 'Recaudo creado','data': serializer.data}, 200)
            else:
                return response({'error': True, 'message': serializer.errors}, 400)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['admin'])
    def patch(self, request, pk):
        try:
            receipt     = Receipt.objects.get(pk=pk)
            serializer  = ReceiptSerializer(receipt, data=request.data, context={'request': request}, partial=True)
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'message': 'Recaudo actualizado', 'data': serializer.data}, 200)
            return response({'error': True, 'message': serializer.errors}, 400)
        except Receipt.DoesNotExist:
            return response({'error': True, 'message': 'Recaudo no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
    @checkRole(['admin'])
    def delete(self, request, pk):
        try:
            receipt       = Receipt.objects.get(pk=pk)
            # update the state of the operation
            receipt.operation.amount          -= receipt.investorInterests
            receipt.operation.opPendingAmount -= receipt.investorInterests
            receipt.operation.amount          -= receipt.additionalInterests
            receipt.operation.opPendingAmount -= receipt.additionalInterests
            receipt.operation.amount          -= receipt.tableInterests
            receipt.operation.opPendingAmount -= receipt.tableInterests
            receipt.operation.payedAmount     -= receipt.payedAmount
            receipt.state = 0
            receipt.operation.save()
            receipt.save()
            return response({'error': False, 'message': 'Recaudo eliminado'}, 200)
        except Receipt.DoesNotExist:
            return response({'error': True, 'message': 'Recaudo no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)


