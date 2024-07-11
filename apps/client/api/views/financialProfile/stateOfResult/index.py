# REST Framework imports
from rest_framework.decorators import APIView
# Models
from apps.client.models import StateOfResult
# Serializers
from apps.client.api.serializers.index import StateOfResultSerializer
# Utils
from apps.base.utils.index import response
# Decorators
from apps.base.decorators.index import checkRole

class StateOfResultAV(APIView):
    @checkRole('admin')
    def get(self, request, pk=None):
        try:
            if pk:
                stateOfResult  = StateOfResult.objects.filter(client=pk)
                serializer     = StateOfResultSerializer(stateOfResult, many=True)
                return response({'error': False, 'data': serializer.data}, 200)
            else:
                stateOfResult  = StateOfResult.objects.filter(state=1)
                serializer     = StateOfResultSerializer(stateOfResult, many=True)
                return response({'error': False, 'data': serializer.data}, 200)
        except StateOfResult.DoesNotExist:
            return response({'error': True, 'message': 'Estado de resultados no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
    @checkRole('admin')
    def post(self, request):
        try:
            serializer = StateOfResultSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'data': serializer.data}, 200)
            else:
                return response({'error': True, 'message': serializer.errors}, 400)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
    @checkRole('admin')
    def patch(self, request, pk=None):
        try:
            stateOfResult  = StateOfResult.objects.get(pk=pk)
            serializer = StateOfResultSerializer(stateOfResult, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'data': serializer.data}, 200)
            else:
                return response({'error': True, 'message': serializer.errors}, 400)
        except StateOfResult.DoesNotExist:
            return response({'error': True, 'message': 'Estado de resultados no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
    @checkRole('admin')
    def delete(self, request, pk=None):
        try:
            stateOfResult = StateOfResult.objects.get(pk=pk)
            stateOfResult = stateOfResult.state = 0
            stateOfResult.save()
            return response({'error': False, 'message': 'Estado de resultados eliminado correctamente'}, 200)
        except StateOfResult.DoesNotExist:
            return response({'error': True, 'message': 'Estado de resultados no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)