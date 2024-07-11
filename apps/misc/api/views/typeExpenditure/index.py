# REST Framework imports
from rest_framework.decorators import APIView
# Models
from apps.misc.models import TypeExpenditure
# Serializers
from apps.misc.api.serializers.index import TypeExpenditureSerializer
# Utils
from apps.base.utils.index import response
# Decorators
from apps.base.decorators.index import checkRole


class TypeExpenditureAV(APIView):
    
        def get(self, request, pk=None):
            try:
                if pk:
                    typeExpenditure = TypeExpenditure.objects.get(pk=pk)
                    serializer  = TypeExpenditureSerializer(typeExpenditure)
                    return response({'error': False, 'data': serializer.data}, 200)
                else:
                    typeExpenditure = TypeExpenditure.objects.filter(state=1).order_by('description')
                    serializer  = TypeExpenditureSerializer(typeExpenditure, many=True)
                    return response({'error': False, 'data': serializer.data}, 200)
            except TypeExpenditure.DoesNotExist:
                return response({'error': True, 'message': 'tipo de egreso no encontrado'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
        @checkRole(['superuser'])
        def post(self, request):
            try:
                serializer = TypeExpenditureSerializer(data=request.data, context={'request':request})
                if serializer.is_valid():
                    serializer.save()
                    return response({'error': False, 'message': 'tipo de egreso creado', 'data': serializer.data}, 200)
                return response({'error': True, 'message': serializer.errors}, 400)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
        @checkRole(['superuser'])
        def patch(self, request, pk):
            try:
                typeExpenditure = TypeExpenditure.objects.get(pk=pk)
                serializer  = TypeExpenditureSerializer(typeExpenditure, data=request.data, context={'request':request})
                if serializer.is_valid():
                    serializer.save()
                    return response({'error': False, 'message': 'tipo de egreso actualizado', 'data': serializer.data}, 200)
                return response({'error': True, 'message': serializer.errors}, 400)
            except TypeExpenditure.DoesNotExist:
                return response({'error': True, 'message': 'tipo de egreso no encontrado'}, 404)
        
        @checkRole(['superuser'])
        def delete(self, request, pk):
            try:
                typeExpenditure = TypeExpenditure.objects.get(pk=pk)
                typeExpenditure.state = 0
                typeExpenditure.save()
                return response({'error': False, 'message': 'tipo de egreso eliminado'}, 204)
            except TypeExpenditure.DoesNotExist:
                return response({'error': True, 'message': 'tipo de egreso no encontrado'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)