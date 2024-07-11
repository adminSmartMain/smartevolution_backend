# REST Framework imports
from rest_framework.decorators import APIView
# Models
from apps.misc.models import TypePeriod
# Serializers
from apps.misc.api.serializers.index import TypePeriodSerializer, TypePeriodReadOnlySerializer
# Utils
from apps.base.utils.index import response
# Decorators
from apps.base.decorators.index import checkRole


class TypePeriodAV(APIView):
    
        def get(self, request, pk=None):
            try:
                if pk:
                    typePeriod    = TypePeriod.objects.get(pk=pk)
                    serializer    = TypePeriodReadOnlySerializer(typePeriod)
                    return response({'error': False, 'data': serializer.data}, 200)
                else:
                    typePeriod    = TypePeriod.objects.filter(state=1).order_by('description')
                    serializer    = TypePeriodReadOnlySerializer(typePeriod, many=True)
                    return response({'error': False, 'data': serializer.data}, 200)
            except TypePeriod.DoesNotExist:
                return response({'error': True, 'message': 'tipo de periodo no encontrado'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
        @checkRole(['superuser'])
        def post(self, request):
            try:
                serializer = TypePeriodSerializer(data=request.data, context={'request':request})
                if serializer.is_valid():
                    serializer.save()
                    return response({'error': False, 'message': 'tipo de periodo creado', 'data': serializer.data}, 200)
                return response({'error': True, 'message': serializer.errors}, 400)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
        @checkRole(['superuser'])
        def patch(self, request, pk):
            try:
                typePeriod = TypePeriod.objects.get(pk=pk)
                serializer  = TypePeriodSerializer(typePeriod, data=request.data, context={'request':request})
                if serializer.is_valid():
                    serializer.save()
                    return response({'error': False, 'message': 'tipo de periodo actualizado', 'data':serializer.data}, 200)
                return response({'error': True, 'message': serializer.errors}, 400)
            except TypePeriod.DoesNotExist:
                return response({'error': True, 'message': 'tipo de periodo no encontrado'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
        
        @checkRole(['superuser'])
        def delete(self, request, pk):
            try:
                typePeriod = TypePeriod.objects.get(pk=pk)
                typePeriod.state = 0
                typePeriod.save()
                return response({'error': False, 'message': 'tipo de periodo eliminado'}, 204)
            except TypePeriod.DoesNotExist:
                return response({'error': True, 'message': 'tipo de periodo no encontrado'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)