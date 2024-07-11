# REST Framework imports
from rest_framework.decorators import APIView
# Models
from apps.client.models import Passives
# Serializers
from apps.client.api.serializers.index import PassivesSerializer
# Utils
from apps.base.utils.index import response
# Decorators
from apps.base.decorators.index import checkRole


class PassivesAV(APIView):
    @checkRole('admin')
    def get(self, request, pk=None):
        try:
            if pk:
                passives   = Passives.objects.filter(client=pk)
                serializer = PassivesSerializer(passives, many=True)
                return response({'error': False, 'data': serializer.data}, 200)
            else:
                passives   = Passives.objects.filter(state=1)
                serializer = PassivesSerializer(passives, many=True)
                return response({'error': False, 'data': serializer.data}, 200)
        except Passives.DoesNotExist:
            return response({'error': True, 'message': 'pasivos no encontrados'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
    @checkRole('admin')
    def post(self, request):
        try:
            serializer = PassivesSerializer(data=request.data)
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
            passive    = Passives.objects.get(pk=pk)
            serializer = PassivesSerializer(passive, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'data': serializer.data}, 200)
            else:
                return response({'error': True, 'message': serializer.errors}, 400)
        except Passives.DoesNotExist:
            return response({'error': True, 'message': 'Pasivo no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
    @checkRole('admin')
    def delete(self, request, pk=None):
        try:
            passive = Passives.objects.get(pk=pk)
            passive.state = 0
            passive.save()
            return response({'error': False, 'message': 'Pasivo eliminado'}, 201)
        except Passives.DoesNotExist:
            return response({'error': True, 'message': 'Pasivo no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)