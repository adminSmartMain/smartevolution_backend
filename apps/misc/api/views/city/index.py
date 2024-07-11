from rest_framework.views import APIView
# Models
from apps.misc.models import City
# Serializers
from apps.misc.api.serializers.index import CitySerializer, CityReadOnlySerializer
# Utils
from apps.base.utils.index import response, BaseAV
# Decorators
from apps.base.decorators.index import checkRole


class CityAV(BaseAV):
        
        def get(self, request, pk=None):
            try:
                if pk:
                    city       = City.objects.filter(department=pk)
                    serializer = CityReadOnlySerializer(city, many=True)
                    return response({'error': False, 'data': serializer.data}, 200)
                else:
                    city       = City.objects.filter(state=1).order_by('description')
                    serializer = CitySerializer(city, many=True)
                    return response({'error': False, 'data': serializer.data}, 200)
            except City.DoesNotExist:
                return response({'error': True, 'message': 'Ciudad no encontrada'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
        @checkRole(['superuser'])
        def post(self, request):
            try:
                serializer = CitySerializer(data=request.data, context={'request':request})
                if serializer.is_valid():
                    serializer.save()
                    return response({'error': False, 'message': 'Ciudad creada', 'data':serializer.data}, 200)
                return response({'error': True, 'message': serializer.errors}, 400)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
        @checkRole(['superuser'])
        def patch(self, request, pk):
            try:
                city       = City.objects.get(pk=pk)
                serializer = CitySerializer(city, data=request.data, context={'request':request})
                if serializer.is_valid():
                    serializer.save()
                    return response({'error': False, 'message': 'Ciudad actualizada', 'data':serializer.data}, 200)
                return response({'error': True, 'message': serializer.errors}, 400)
            except City.DoesNotExist:
                return response({'error': True, 'message': 'Ciudad no encontrada'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
        
        @checkRole(['superuser'])
        def delete(self, request, pk):
            try:
                city = City.objects.get(pk=pk)
                city.state = 0
                city.save()
                return response({'error': False, 'message': 'Ciudad eliminada'}, 204)
            except City.DoesNotExist:
                return response({'error': True, 'message': 'Ciudad no encontrada'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)