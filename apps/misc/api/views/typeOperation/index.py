# REST Framework imports
from rest_framework.decorators import APIView
# Models
from apps.misc.models import TypeOperation
# Serializers
from apps.misc.api.serializers.index import TypeOperationSerializer
# Utils
from apps.base.utils.index import response
# Decorators
from apps.base.decorators.index import checkRole


class TypeOperationAV(APIView):
    
        def get(self, request, pk=None):
            try:
                if pk:
                    typeOperation = TypeOperation.objects.get(pk=pk)
                    serializer    = TypeOperationSerializer(typeOperation)
                    return response({'error': False, 'data': serializer.data}, 200)
                else:
                    typeOperation = TypeOperation.objects.filter(state=1).order_by('description')
                    serializer    = TypeOperationSerializer(typeOperation, many=True)
                    return response({'error': False, 'data': serializer.data}, 200)
            except TypeOperation.DoesNotExist:
                return response({'error': True, 'message': 'Tipo de operacion no encontrado'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
        @checkRole(['superuser'])
        def post(self, request):
            try:
                serializer = TypeOperationSerializer(data=request.data, context={'request':request})
                if serializer.is_valid():
                    serializer.save()
                    return response({'error': False, 'message': 'Tipo de operacion creado', 'data': serializer.data}, 200)
                return response({'error': True, 'message': serializer.errors}, 400)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
        @checkRole(['superuser'])
        def patch(self, request, pk):
            try:
                typeOperation = TypeOperation.objects.get(pk=pk)
                serializer  = TypeOperationSerializer(typeOperation, data=request.data, context={'request':request})
                if serializer.is_valid():
                    serializer.save()
                    return response({'error': False, 'message': 'tipo de operacion actualizado', 'data':serializer.data}, 200)
                return response({'error': True, 'message': serializer.errors}, 400)
            except TypeOperation.DoesNotExist:
                return response({'error': True, 'message': 'Tipo de operacion no encontrado'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
        
        @checkRole(['superuser'])
        def delete(self, request, pk):
            try:
                typeOperation = TypeOperation.objects.get(pk=pk)
                typeOperation.state = 0
                typeOperation.save()
                return response({'error': False, 'message': 'Tipo de operacion eliminado'}, 204)
            except TypeOperation.DoesNotExist:
                return response({'error': True, 'message': 'Tipo de operacion no encontrado'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)