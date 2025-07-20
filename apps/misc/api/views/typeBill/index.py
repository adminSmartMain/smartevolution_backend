from rest_framework.views import APIView
from rest_framework import status
from apps.misc.models import TypeBill
from apps.misc.api.serializers.typeBill.index import TypeBillSerializer
from apps.base.utils.index import response
from apps.base.decorators.index import checkRole




class TypeBillAV(APIView):
    def get(self, request, pk=None):
        try:
            if pk:
                # Detalle individual
                type_bill = TypeBill.objects.get(pk=pk)
                serializer = TypeBillSerializer(type_bill)
                return response({'data': serializer.data})
            else:
                # Listado
                type_bills = TypeBill.objects.all().order_by('-created_at')
                serializer = TypeBillSerializer(type_bills, many=True)
                return response({'data': serializer.data},status=200)
                
        except TypeBill.DoesNotExist:
            return response({'error': 'TypeBill no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @checkRole(['admin'])
    def post(self, request):
        serializer = TypeBillSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return response({'data': serializer.data}, status=status.HTTP_201_CREATED)
        return response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @checkRole(['admin'])
    def patch(self, request, pk=None):
        if not pk:
            return response({'error': 'Se requiere ID'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            type_bill = TypeBill.objects.get(pk=pk)
            serializer = TypeBillSerializer(type_bill, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                return response({'data': serializer.data})
            return response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            
        except TypeBill.DoesNotExist:
            return response({'error': 'TypeBill no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    @checkRole(['admin'])
    def delete(self, request, pk=None):
        if not pk:
            return response({'error': 'Se requiere ID'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            type_bill = TypeBill.objects.get(pk=pk)
            type_bill.delete()
            return response(status=status.HTTP_204_NO_CONTENT)
        except TypeBill.DoesNotExist:
            return response({'error': 'TypeBill no encontrado'}, status=status.HTTP_404_NOT_FOUND)