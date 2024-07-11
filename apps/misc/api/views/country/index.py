# REST Framework imports
from rest_framework.decorators import APIView
# Models
from apps.misc.models import Country
# Serializers
from apps.misc.api.serializers.index import CountrySerializer
# Utils
from apps.base.utils.index import response
# Decorators
from apps.base.decorators.index import checkRole


class CountryAV(APIView):

    def get(self, request, pk=None):
        try:
            if pk:
                country    = Country.objects.get(pk=pk)
                serializer = CountrySerializer(country)
            else:
                countries  = Country.objects.filter(state=1).order_by('name_es')
                serializer = CountrySerializer(countries, many=True)
            return response({'error': False, 'data': serializer.data}, 200)
        except Country.DoesNotExist:
            return response({'error': True, 'message': 'país no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['superuser'])
    def post(self, request):
        try:
            serializer = CountrySerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'data': serializer.data}, 200)
            return response({'error': True, 'message': 'país creado', 'data': serializer.errors}, 400)
        except Country.DoesNotExist:
            return response({'error': True, 'message': 'país no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['superuser'])
    def patch(self, request, pk):
        try:
            country = Country.objects.get(pk=pk)
            serializer = CountrySerializer(country, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'data': serializer.data}, 200)
            return response({'error': True, 'message': 'país actualizado', 'data': serializer.errors}, 400)
        except Country.DoesNotExist:
            return response({'error': True, 'message': 'país no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['superuser'])
    def delete(self, request, pk):
        try:
            country = Country.objects.get(pk=pk)
            country.state = 0
            country.save()
            return response({'error': False, 'data': 'país eliminado'}, 204)
        except Country.DoesNotExist:
            return response({'error': True, 'message': 'país no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
