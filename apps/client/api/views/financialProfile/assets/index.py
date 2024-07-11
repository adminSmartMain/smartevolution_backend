# REST Framework imports
from rest_framework.decorators import APIView
# Models
from apps.client.models import Assets
# Serializers
from apps.client.api.serializers.index import AssetsSerializer
# Utils
from apps.base.utils.index import response
# Decorators
from apps.base.decorators.index import checkRole


class AssetsAV(APIView):
    @checkRole('admin')
    def get(self, request, pk=None):
        try:
            if pk:
                assets     = Assets.objects.filter(client=pk)
                serializer = AssetsSerializer(assets, many=True)
                return response({'error': False, 'data': serializer.data}, 200)
            else:
                assets     = Assets.objects.filter(state=1)
                serializer = AssetsSerializer(assets, many=True)
                return response({'error': False, 'data': serializer.data}, 200)
        except Assets.DoesNotExist:
            return response({'error': True, 'message': 'activos no encontrados'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
    @checkRole('admin')
    def post(self, request):
        try:
            serializer = AssetsSerializer(data=request.data)
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
            asset      = Assets.objects.get(pk=pk)
            serializer = AssetsSerializer(asset, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'data': serializer.data}, 200)
            else:
                return response({'error': True, 'message': serializer.errors}, 400)
        except Assets.DoesNotExist:
            return response({'error': True, 'message': 'Activo no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
    @checkRole('admin')
    def delete(self, request, pk=None):
        try:
            asset = Assets.objects.get(pk=pk)
            asset.state = 0
            asset.save()
            return response({'error': False, 'message': 'Activo eliminado correctamente'}, 200)
        except Assets.DoesNotExist:
            return response({'error': True, 'message': 'Activo no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
