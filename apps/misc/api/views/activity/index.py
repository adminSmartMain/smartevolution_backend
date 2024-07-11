# REST Framework imports
from rest_framework.decorators import APIView
# Models
from apps.misc.models import Activity
# Serializers
from apps.misc.api.serializers.index import ActivitySerializer
# Utils
from apps.base.utils.index import response
# Decorators
from apps.base.decorators.index import checkRole


class ActivityAV(APIView):

    def get(self, request, pk=None):
            try:
                if pk:
                    activity   = Activity.objects.get(pk=pk)
                    serializer = ActivitySerializer(activity)
                    return response({'error': False, 'data': serializer.data}, 200)
                else:
                    activities = Activity.objects.filter(state=1).order_by('description')
                    serializer = ActivitySerializer(activities, many=True)
                    return response({'error': False, 'data': serializer.data}, 200)
            except Activity.DoesNotExist:
                return response({'error': True, 'message': 'actividad no encontrada'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['superuser'])
    def post(self, request):
            try:
                serializer = ActivitySerializer(data=request.data, context={'request': request})
                if serializer.is_valid():
                    serializer.save()
                    return response({'error': False, 'message': 'actividad creada','data': serializer.data}, 200)
                return response({'error': True, 'message': serializer.errors}, 400)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['superuser'])
    def patch(self, request, pk):
            try:
                activity = Activity.objects.get(pk=pk)
                serializer = ActivitySerializer(activity, data=request.data, context={'request': request})
                if serializer.is_valid():
                    serializer.save()
                    return response({'error': False, 'message': 'actividad actualizada', 'data': serializer.data}, 200)
                return response({'error': True, 'message': serializer.errors}, 400)
            except Activity.DoesNotExist:
                return response({'error': True, 'message': 'actividad no encontrada'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['superuser'])
    def delete(self, request, pk):
            try:
                activity = Activity.objects.get(pk=pk)
                activity.state = 0
                activity.save()
                return response({'error': False, 'message': 'actividad eliminada'}, 204)
            except Activity.DoesNotExist:
                return response({'error': True, 'message': 'actividad no encontrada'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
