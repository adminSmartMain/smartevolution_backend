# REST Framework imports
from rest_framework.decorators import APIView
# Models
from apps.misc.models import TypeCLient
# Serializers
from apps.misc.api.serializers.index import TypeClientSerializer
# Utils
from apps.base.utils.index import response
# Decorators
from apps.base.decorators.index import checkRole


class TypeClientAV(APIView):
    
        def get(self, request, pk=None):
            try:
                if pk:
                    type_client = TypeCLient.objects.get(pk=pk)
                    serializer  = TypeClientSerializer(type_client)
                    return response({'error': False, 'data': serializer.data}, 200)
                else:
                    type_client = TypeCLient.objects.filter(state=1).order_by('description')
                    serializer  = TypeClientSerializer(type_client, many=True)
                    return response({'error': False, 'data': serializer.data}, 200)
            except TypeCLient.DoesNotExist:
                return response({'error': True, 'message': 'tipo de cliente no encontrado'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
        @checkRole(['superuser'])
        def post(self, request):
            try:
                serializer = TypeClientSerializer(data=request.data, context={'request':request})
                if serializer.is_valid():
                    serializer.save()
                    return response({'error': False, 'message': 'tipo de cliente creado', 'data': serializer.data}, 200)
                return response({'error': True, 'message': serializer.errors}, 400)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
        @checkRole(['superuser'])
        def patch(self, request, pk):
            try:
                type_client = TypeCLient.objects.get(pk=pk)
                serializer  = TypeClientSerializer(type_client, data=request.data, context={'request':request})
                if serializer.is_valid():
                    serializer.save()
                    return response({'error': False, 'message': 'tipo de cliente actualizado', 'data': serializer.data}, 200)
                return response({'error': True, 'message': serializer.errors}, 400)
            except TypeCLient.DoesNotExist:
                return response({'error': True, 'message': 'tipo de cliente no encontrado'}, 404)
        
        @checkRole(['superuser'])
        def delete(self, request, pk):
            try:
                type_client = TypeCLient.objects.get(pk=pk)
                type_client.state = 0
                type_client.save()
                return response({'error': False, 'message': 'tipo de cliente eliminado'}, 204)
            except TypeCLient.DoesNotExist:
                return response({'error': True, 'message': 'tipo de cliente no encontrado'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)