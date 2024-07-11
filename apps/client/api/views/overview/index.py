# REST Framework imports
from rest_framework.decorators import APIView
# Models
from apps.client.models import Overview
# Serializers
from apps.client.api.serializers.index import OverviewSerializer
# Utils
from apps.base.utils.index import response
# Decorators
from apps.base.decorators.index import checkRole


class OverviewAV(APIView):

    @checkRole(['admin'])
    def get(self, request, pk=None):
        try:
            if pk:
                overview   = Overview.objects.get(id=pk)
                serializer = OverviewSerializer(overview)
                return response({'error': False, 'data': serializer.data}, 200)
            else:
                overview   = Overview.objects.all()
                serializer = OverviewSerializer(overview, many=True)
                return response({'error': False, 'data': serializer.data}, 200)
        except Overview.DoesNotExist:
            return response({'error': True, 'message': 'resumen financiero no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
        
    @checkRole(['admin'])
    def post(self, request):
        try:
            serializer = OverviewSerializer(data=request.data, context={'request':request})
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'message': 'resumen financiero creado', 'data': serializer.data}, 200)
            return response({'error': True, 'message': serializer.errors}, 400)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
    @checkRole(['admin'])
    def patch(self, request, pk):
        try:
            overview   = Overview.objects.get(id=pk)
            serializer = OverviewSerializer(overview, data=request.data, context={'request':request}, partial=True)
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'message': 'resumen financiero actualizado','data':serializer.data}, 200)
            return response({'error': True, 'message': serializer.errors}, 400)
        except Overview.DoesNotExist:
            return response({'error': True, 'message': 'resumen financiero no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
    @checkRole(['admin'])
    def delete(self, request, pk):
        try:
            overview       = Overview.objects.get(id=pk)
            overview.state = 0
            overview.save()
            return response({'error': False, 'message': 'resumen financiero eliminado'}, 200)
        except Overview.DoesNotExist:
            return response({'error': True, 'message': 'resumen financiero no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

