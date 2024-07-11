# REST Framework imports
from rest_framework.decorators import APIView
# Models
from apps.misc.models import CIIU
# Serializers
from apps.misc.api.serializers.index import CIIUSerializer, CIIUReadOnlySerializer
# Utils
from apps.base.utils.index import response
# Decorators
from apps.base.decorators.index import checkRole


class CIIUAV(APIView):

    def get(self, request, pk=None):
        try:
            if pk:
                ciiu       = CIIU.objects.get(pk=pk)
                serializer = CIIUReadOnlySerializer(ciiu)
                return response({'error': False, 'data': serializer.data}, 200)
            else:
                ciiu       = CIIU.objects.filter(state=1).order_by('code')
                serializer = CIIUReadOnlySerializer(ciiu, many=True)
                return response({'error': False, 'data': serializer.data}, 200)
        except CIIU.DoesNotExist:
            return response({'error': True, 'message': 'CIIU no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['superuser'])
    def post(self, request):
        try:
            serializer = CIIUSerializer(
                data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'message': 'CIIU creado', 'data': serializer.data}, 200)
            return response({'error': True, 'message': serializer.errors}, 400)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['superuser'])
    def patch(self, request, pk):
        try:
            ciiu = CIIU.objects.get(pk=pk)
            serializer = CIIUSerializer(
                ciiu, data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'message': 'CIIU actualizado', 'data': serializer.data}, 200)
            return response({'error': True, 'message': serializer.errors}, 400)
        except CIIU.DoesNotExist:
            return response({'error': True, 'message': 'CIIU no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['superuser'])
    def delete(self, request, pk):
        try:
            ciiu = CIIU.objects.get(pk=pk)
            ciiu.state = 0
            ciiu.save()
            return response({'error': False, 'message': 'CIIU eliminado'}, 204)
        except CIIU.DoesNotExist:
            return response({'error': True, 'message': 'CIIU no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
