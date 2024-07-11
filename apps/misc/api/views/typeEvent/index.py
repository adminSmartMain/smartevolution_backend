# REST Framework imports
from rest_framework.decorators import APIView
# Models
from apps.misc.models import TypeEvent
# Serializers
from apps.misc.api.serializers.index import TypeEventSerializer
# Utils
from apps.base.utils.index import response
# Decorators
from apps.base.decorators.index import checkRole


class TypeEventAV(APIView):
    
        def get(self, request, pk=None):
            try:
                if pk:
                    typeEvent  = TypeEvent.objects.get(pk=pk)
                    serializer = TypeEventSerializer(typeEvent)
                    return response({'error': False, 'data': serializer.data}, 200)
                else:
                    typeEvent  = TypeEvent.objects.filter(state=1).order_by('description')
                    serializer = TypeEventSerializer(typeEvent, many=True)
                    return response({'error': False, 'data': serializer.data}, 200)
            except TypeEvent.DoesNotExist:
                return response({'error': True, 'message': 'Tipo de evento no encontrado'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
        @checkRole(['superuser'])
        def post(self, request):
            try:
                serializer = TypeEventSerializer(data=request.data, context={'request':request})
                if serializer.is_valid():
                    serializer.save()
                    return response({'error': False, 'message': 'Tipo de evento creado', 'data': serializer.data}, 200)
                return response({'error': True, 'message': serializer.errors}, 400)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
        @checkRole(['superuser'])
        def patch(self, request, pk):
            try:
                typeEvent = TypeEvent.objects.get(pk=pk)
                serializer  = TypeEventSerializer(typeEvent, data=request.data, context={'request':request})
                if serializer.is_valid():
                    serializer.save()
                    return response({'error': False, 'message': 'tipo de evento actualizado', 'data':serializer.data}, 200)
                return response({'error': True, 'message': serializer.errors}, 400)
            except TypeEvent.DoesNotExist:
                return response({'error': True, 'message': 'Tipo de evento no encontrado'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
        
        @checkRole(['superuser'])
        def delete(self, request, pk):
            try:
                typeEvent = TypeEvent.objects.get(pk=pk)
                typeEvent.state = 0
                typeEvent.save()
                return response({'error': False, 'message': 'Tipo de evento eliminado'}, 204)
            except TypeEvent.DoesNotExist:
                return response({'error': True, 'message': 'Tipo de evento no encontrado'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)