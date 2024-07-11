# REST Framework imports
from rest_framework.decorators import APIView
# Models
from apps.misc.models import PeriodRange
# Serializers
from apps.misc.api.serializers.index import PeriodRangeSerializer
# Utils
from apps.base.utils.index import response
# Decorators
from apps.base.decorators.index import checkRole


class PeriodRangeAV(APIView):
    
        def get(self, request, pk=None):
            try:
                if pk:
                    periodRange   = PeriodRange.objects.get(pk=pk)
                    serializer    = PeriodRangeSerializer(periodRange)
                    return response({'error': False, 'data': serializer.data}, 200)
                else:
                    periodRange   = PeriodRange.objects.filter(state=1).order_by('description')
                    serializer    = PeriodRangeSerializer(periodRange, many=True)
                    return response({'error': False, 'data': serializer.data}, 200)
            except periodRange.DoesNotExist:
                return response({'error': True, 'message': 'rango de periodo no encontrado'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
        @checkRole(['superuser'])
        def post(self, request):
            try:
                serializer = PeriodRangeSerializer(data=request.data, context={'request':request})
                if serializer.is_valid():
                    serializer.save()
                    return response({'error': False, 'message': 'rango de periodo creado', 'data': serializer.data}, 200)
                return response({'error': True, 'message': serializer.errors}, 400)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
        @checkRole(['superuser'])
        def patch(self, request, pk):
            try:
                periodRange = PeriodRange.objects.get(pk=pk)
                serializer  = PeriodRangeSerializer(periodRange, data=request.data, context={'request':request})
                if serializer.is_valid():
                    serializer.save()
                    return response({'error': False, 'message': 'rango de periodo actualizado', 'data':serializer.data}, 200)
                return response({'error': True, 'message': serializer.errors}, 400)
            except periodRange.DoesNotExist:
                return response({'error': True, 'message': 'rango de periodo no encontrado'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
        
        @checkRole(['superuser'])
        def delete(self, request, pk):
            try:
                periodRange = PeriodRange.objects.get(pk=pk)
                periodRange.state = 0
                periodRange.save()
                return response({'error': False, 'message': 'rango de periodo eliminado'}, 204)
            except periodRange.DoesNotExist:
                return response({'error': True, 'message': 'rango de periodo no encontrado'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)