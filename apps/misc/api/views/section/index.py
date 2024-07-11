# REST Framework imports
from rest_framework.decorators import APIView
# Models
from apps.misc.models import Section
# Serializers
from apps.misc.api.serializers.index import SectionSerializer
# Utils
from apps.base.utils.index import response
# Decorators
from apps.base.decorators.index import checkRole


class SectionAV(APIView):

    def get(self, request, pk=None):
        try:
            if pk:
                section = Section.objects.get(pk=pk)
                serializer = SectionSerializer(section)
                return response({'error': False, 'data': serializer.data}, 200)
            else:
                section = Section.objects.filter(state=1).order_by('description')
                serializer = SectionSerializer(section, many=True)
                return response({'error': False, 'data': serializer.data}, 200)
        except Section.DoesNotExist:
            return response({'error': True, 'message': 'Sección no encontrada'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['superuser'])
    def post(self, request):
        try:
            serializer = SectionSerializer(
                data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'message': 'Sección creada', 'data': serializer.data}, 200)
            return response({'error': True, 'message': serializer.errors}, 400)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['superuser'])
    def patch(self, request, pk):
        try:
            section = Section.objects.get(pk=pk)
            serializer = SectionSerializer(
                section, data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'message': 'Sección actualizada', 'data': serializer.data}, 200)
            return response({'error': True, 'message': serializer.errors}, 400)
        except Section.DoesNotExist:
            return response({'error': True, 'message': 'Sección no encontrada'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['superuser'])
    def delete(self, request, pk):
        try:
            section = Section.objects.get(pk=pk)
            section.state = 0
            section.save()
            return response({'error': False, 'message': 'Sección eliminada'}, 204)
        except Section.DoesNotExist:
            return response({'error': True, 'message': 'Sección no encontrada'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
