# REST Framework imports
from rest_framework.decorators import APIView
# Models
from apps.client.models import Patrimony
# Serializers
from apps.client.api.serializers.index import PatrimonySerializer
# Utils
from apps.base.utils.index import response
# Decorators
from apps.base.decorators.index import checkRole


class PatrimonyAV(APIView):
    @checkRole('admin')
    def get(self, request, pk=None):
        try:
            if pk:
                patrimony  = Patrimony.objects.filter(client=pk)
                serializer = PatrimonySerializer(patrimony, many=True)
                return response({'error': False, 'data': serializer.data}, 200)
            else:
                patrimony  = Patrimony.objects.filter(state=1)
                serializer = PatrimonySerializer(patrimony, many=True)
                return response({'error': False, 'data': serializer.data}, 200)
        except Patrimony.DoesNotExist:
            return response({'error': True, 'message': 'patrimonio no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
    @checkRole('admin')
    def post(self, request):
        try:
            serializer = PatrimonySerializer(data=request.data)
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
            patrimony  = Patrimony.objects.get(pk=pk)
            serializer = PatrimonySerializer(patrimony, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'data': serializer.data}, 200)
            else:
                return response({'error': True, 'message': serializer.errors}, 400)
        except Patrimony.DoesNotExist:
            return response({'error': True, 'message': 'Patrimonio no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
    @checkRole('admin')
    def delete(self, request, pk=None):
        try:
            patrimony = Patrimony.objects.get(pk=pk)
            patrimony.state = 0
            patrimony.save()
            return response({'error': False, 'message': 'Patrimonio eliminado correctamente'}, 200)
        except Patrimony.DoesNotExist:
            return response({'error': True, 'message': 'Patrimonio no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)