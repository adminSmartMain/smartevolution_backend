# REST Framework imports
from rest_framework.decorators import APIView
# Models
from apps.client.models import LegalRepresentative
# Serializers
from apps.client.api.serializers.index import LegalRepresentativeSerializer
# Utils
from apps.base.utils.index import response
# Decorators
from apps.base.decorators.index import checkRole

class LegalRepresentativeAV(APIView):

    @checkRole('admin')
    def get(self, request, pk=None):
        try:
            if pk:
                LegalRepresentative = LegalRepresentative.objects.get(pk=pk)
                serializer          = LegalRepresentativeSerializer(LegalRepresentative)
                return response({'error': False, 'data': serializer.data}, 200)
            else:
                LegalRepresentative = LegalRepresentative.objects.filter(state=1)
                serializer = LegalRepresentativeSerializer(LegalRepresentative, many=True)
                return response({'error': False, 'data': serializer.data}, 200)
        except LegalRepresentative.DoesNotExist:
            return response({'error': True, 'message': 'Representante Legal no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
    @checkRole('admin')
    def post(self, request):
        try:
            serializer = LegalRepresentativeSerializer(data=request.data)
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
            LegalRepresentative = LegalRepresentative.objects.get(pk=pk)
            serializer          = LegalRepresentativeSerializer(LegalRepresentative, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'data': serializer.data}, 200)
            else:
                return response({'error': True, 'message': serializer.errors}, 400)
        except LegalRepresentative.DoesNotExist:
            return response({'error': True, 'message': 'Representante Legal no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
    @checkRole('admin')
    def delete(self, request, pk=None):
        try:
            LegalRepresentative = LegalRepresentative.objects.get(pk=pk)
            LegalRepresentative.state = 0
            LegalRepresentative.save()
            return response({'error': False, 'message': 'Representante eliminado'}, 200)
        except LegalRepresentative.DoesNotExist:
            return response({'error': True, 'message': 'Representante Legal no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
