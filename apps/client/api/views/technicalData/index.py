# REST Framework imports
from rest_framework.decorators import APIView
# Models
from apps.client.models import FinancialCentral
# Serializers
from apps.client.api.serializers.index import FinancialCentralSerializer
# Utils
from apps.base.utils.index import response
# Decorators
from apps.base.decorators.index import checkRole


class technicalDataAV(APIView):

    @checkRole(['admin'])
    def get(self, request, pk=None):
        try:
            if pk:
                financialCentral = FinancialCentral.objects.get(id=pk)
                serializer       = FinancialCentralSerializer(financialCentral)
                return response({'error': False, 'data': serializer.data}, 200)
            else:
                financialCentral = FinancialCentral.objects.all()
                serializer       = FinancialCentralSerializer(financialCentral, many=True)
                return response({'error': False, 'data': serializer.data}, 200)
        except FinancialCentral.DoesNotExist:
            return response({'error': True, 'message': 'ficha técnica no encontrada'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
        
    @checkRole(['admin'])
    def post(self, request):
        try:
            for x in request.data['data']:
                serializer = FinancialCentralSerializer(data=x, context={'request':request})
                if serializer.is_valid():
                    serializer.save()
                else:
                    return response({'error': True, 'message': serializer.errors}, 400)
            return response({'error': False, 'message': 'ficha técnica creada', 'data':serializer.data}, 200)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
    @checkRole(['admin'])
    def patch(self, request, pk):
        try:
            financialCentral = FinancialCentral.objects.get(id=pk)
            serializer  = FinancialCentralSerializer(financialCentral, data=request.data, context={'request':request}, partial=True)
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'message': 'ficha técnica actualizada','data':serializer.data}, 200)
            return response({'error': True, 'message': serializer.errors}, 400)
        except FinancialCentral.DoesNotExist:
            return response({'error': True, 'message': 'ficha técnica no encontrada'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
    @checkRole(['admin'])
    def delete(self, request, pk):
        try:
            financialCentral       = FinancialCentral.objects.get(id=pk)
            financialCentral.state = 0
            financialCentral.save()
            return response({'error': False, 'message': 'ficha técnica eliminada'}, 200)
        except FinancialCentral.DoesNotExist:
            return response({'error': True, 'message': 'ficha técnica no encontrada'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

