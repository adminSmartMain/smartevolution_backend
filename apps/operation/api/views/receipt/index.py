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
from django.db.models import Q, Count
import logging
# Configurar el logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Crear un handler de consola y definir el nivel
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Crear un formato para los mensajes de log
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Añadir el handler al logger
logger.addHandler(console_handler)
class ReceiptAV(BaseAV):

    @checkRole(['admin'])
    def get(self, request, pk=None):
        try:
            
            if len(request.query_params) > 0:
                
                if request.query_params.get('id') != '' and len(request.query_params) == 1: #and request.query_params.get('opId_billId') in [None, ''] and request.query_params.get('statusReceipt') in [None, ''] and request.query_params.get('startDate') in [None, ''] and request.query_params.get('endDate') in [None, '']:
                
                    receipts    = Receipt.objects.filter(id=request.query_params.get('id'))
                    page        = self.paginate_queryset(receipts)
                    if page is not None:
                        serializer = ReceiptReadOnlySerializer(page, many=True)
                        return self.get_paginated_response(serializer.data)
                
                elif request.query_params.get('opId') != '' and len(request.query_params) == 2: #and request.query_params.get('opId_billId') in [None, ''] and request.query_params.get('statusReceipt') in [None, ''] and request.query_params.get('startDate') in [None, ''] and request.query_params.get('endDate') in [None, '']:
              
                    receipts    = Receipt.objects.filter(operation__opId=request.query_params.get('opId'))
                    page        = self.paginate_queryset(receipts)
                    if page is not None:
                        serializer = ReceiptReadOnlySerializer(page, many=True)
                        return self.get_paginated_response(serializer.data)
               

                elif request.query_params.get('opId_billId') not in [None, ''] and request.query_params.get('statusReceipt') in [None, ''] and request.query_params.get('startDate') in [None, ''] and request.query_params.get('endDate') in [None, '']:
                    try:
                        search_value = request.query_params.get('opId_billId', '').strip()
                        
                        
                        # Intentar buscar como opId (numérico)
                        try:
                            op_id_value = int(search_value)
                            receipts_by_opid = Receipt.objects.filter(operation__opId=op_id_value)
                        except (ValueError, TypeError):
                            receipts_by_opid = Receipt.objects.none()
                        
                        # Buscar como billId (texto)
                        receipts_by_billid = Receipt.objects.filter(operation__bill__billId=search_value)
                        
                        # Combinar resultados
                        receipts = receipts_by_opid | receipts_by_billid
                        
                        page = self.paginate_queryset(receipts)
                        if page is not None:
                            serializer = ReceiptReadOnlySerializer(page, many=True)
                            return self.get_paginated_response(serializer.data)
                            
                    except Exception as e:
                        logger.error(f"Error filtering receipts: {str(e)}")
                     
                     
                elif request.query_params.get('opId_billId') != '' and request.query_params.get('statusReceipt')!='' and request.query_params.get('startDate')=='' and request.query_params.get('endDate')=='':
                    try:
                        search_value = request.query_params.get('opId_billId', '').strip()
                        
                        # Intentar buscar como opId (numérico)
                        try:
                            op_id_value = int(search_value)
                            receipts_by_opid = Receipt.objects.filter(operation__opId=op_id_value,
                                                         typeReceipt_id=request.query_params.get('statusReceipt'))
                        except (ValueError, TypeError):
                            receipts_by_opid = Receipt.objects.none()
                        
                        # Buscar como billId (texto)
                        receipts_by_billid = Receipt.objects.filter(operation__bill__billId=search_value,
                                                         typeReceipt_id=request.query_params.get('statusReceipt'))
                        
                        # Combinar resultados
                        receipts = receipts_by_opid | receipts_by_billid
                        
                        page = self.paginate_queryset(receipts)
                        if page is not None:
                            serializer = ReceiptReadOnlySerializer(page, many=True)
                            return self.get_paginated_response(serializer.data)
                            
                    except Exception as e:
                        logger.error(f"Error filtering receipts: {str(e)}")
                elif request.query_params.get('opId_billId') != '' and request.query_params.get('statusReceipt')!='' and request.query_params.get('startDate')!='' and request.query_params.get('endDate')!='':
                    try:
                        search_value = request.query_params.get('opId_billId', '').strip()
                        
                        
                        # Intentar buscar como opId (numérico)
                        try:
                            op_id_value = int(search_value)
                            receipts_by_opid = Receipt.objects.filter(operation__opId=op_id_value,
                                                        date__gte=request.query_params.get('startDate'),
                                                        date__lte=request.query_params.get('endDate'),
                                                        typeReceipt_id=request.query_params.get('statusReceipt'))
                        except (ValueError, TypeError):
                            receipts_by_opid = Receipt.objects.none()
                        
                        # Buscar como billId (texto)
                        receipts_by_billid = Receipt.objects.filter(operation__bill__billId=search_value,
                                                        date__gte=request.query_params.get('startDate'),
                                                        date__lte=request.query_params.get('endDate'),
                                                        typeReceipt_id=request.query_params.get('statusReceipt'))
                        
                        # Combinar resultados
                        receipts = receipts_by_opid | receipts_by_billid
                        
                        page = self.paginate_queryset(receipts)
                        if page is not None:
                            serializer = ReceiptReadOnlySerializer(page, many=True)
                            return self.get_paginated_response(serializer.data)
                            
                    except Exception as e:
                        logger.error(f"Error filtering receipts: {str(e)}")
                elif request.query_params.get('opId_billId') != '' and request.query_params.get('statusReceipt')=='' and request.query_params.get('startDate')!='' and request.query_params.get('endDate')!='':
                    try:
                        search_value = request.query_params.get('opId_billId', '').strip()
                        
                        
                        # Intentar buscar como opId (numérico)
                        try:
                            op_id_value = int(search_value)
                            receipts_by_opid = Receipt.objects.filter(operation__opId=op_id_value,
                                                        date__gte=request.query_params.get('startDate'),
                                                        date__lte=request.query_params.get('endDate'),
                                                        )
                        except (ValueError, TypeError):
                            receipts_by_opid = Receipt.objects.none()
                        
                        # Buscar como billId (texto)
                        receipts_by_billid = Receipt.objects.filter(operation__bill__billId=search_value,
                                                        date__gte=request.query_params.get('startDate'),
                                                        date__lte=request.query_params.get('endDate'),
                                                        )
                        
                        # Combinar resultados
                        receipts = receipts_by_opid | receipts_by_billid
                        
                        page = self.paginate_queryset(receipts)
                        if page is not None:
                            serializer = ReceiptReadOnlySerializer(page, many=True)
                            return self.get_paginated_response(serializer.data)
                            
                    except Exception as e:
                        logger.error(f"Error filtering receipts: {str(e)}")
                elif request.query_params.get('opId_billId') == '' and request.query_params.get('statusReceipt')!='' and request.query_params.get('startDate')!='' and request.query_params.get('endDate')!='':
                    
                    receipts    = Receipt.objects.filter(
                                                         date__gte=request.query_params.get('startDate'),
                                                            date__lte=request.query_params.get('endDate'),
                                                            typeReceipt_id=request.query_params.get('statusReceipt'))
                    page        = self.paginate_queryset(receipts)
                    if page is not None:
                        serializer = ReceiptReadOnlySerializer(page, many=True)
                        return self.get_paginated_response(serializer.data)
                elif request.query_params.get('opId_billId') == '' and request.query_params.get('statusReceipt')=='' and request.query_params.get('startDate')!='' and request.query_params.get('endDate')!='':
                    
                    receipts    = Receipt.objects.filter(date__gte=request.query_params.get('startDate'),
                                                        date__lte=request.query_params.get('endDate'))
                    page        = self.paginate_queryset(receipts)
                    if page is not None:
                        serializer = ReceiptReadOnlySerializer(page, many=True)
                        return self.get_paginated_response(serializer.data)
                elif request.query_params.get('opId_billId') == '' and request.query_params.get('statusReceipt')!='' and request.query_params.get('startDate')=='' and request.query_params.get('endDate')=='':
                    
                    receipts    = Receipt.objects.filter(typeReceipt_id=request.query_params.get('statusReceipt'))
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


