# REST Framework imports
from rest_framework.decorators import APIView
# Models
from apps.misc.models import TypeIdentity
# Serializers
from apps.misc.api.serializers.index import TypeIdentitySerializer
# Utils
from apps.base.utils.index import response
# Decorators
from apps.base.decorators.index import checkRole


class TypeIdentityAV(APIView):

    def get(self, request, pk=None):
        try:
            if pk:
                type_identity = TypeIdentity.objects.get(pk=pk)
                serializer    = TypeIdentitySerializer(type_identity)
                return response({'error': False, 'data': serializer.data}, 200)
            else:
                type_identity = TypeIdentity.objects.filter(state=1).order_by('description')
                serializer    = TypeIdentitySerializer(type_identity, many=True)
                return response({'error': False, 'data': serializer.data}, 200)
        except TypeIdentity.DoesNotExist:
            return response({'error': True, 'message': 'TypeIdentity not found'}, 500)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['superuser'])
    def post(self, request):
        try:
            serializer = TypeIdentitySerializer(
                data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'message': 'TypeIdentity created', 'data': serializer.data}, 200)
            return response({'error': True, 'message': serializer.errors}, 400)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['superuser'])
    def patch(self, request, pk):
        try:
            type_identity = TypeIdentity.objects.get(pk=pk)
            serializer = TypeIdentitySerializer(type_identity, data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'message': 'TypeIdentity updated', 'data': serializer.data}, 200)
            return response({'error': True, 'message': serializer.errors}, 400)
        except TypeIdentity.DoesNotExist:
            return response({'error': True, 'message': 'TypeIdentity not found'}, 500)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['superuser'])
    def delete(self, request, pk):
        try:
            type_identity = TypeIdentity.objects.get(pk=pk)
            type_identity.state = 0
            type_identity.save()
            return response({'error': False, 'message': 'TypeIdentity deleted'}, 204)
        except TypeIdentity.DoesNotExist:
            return response({'error': True, 'message': 'TypeIdentity not found'}, 500)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
