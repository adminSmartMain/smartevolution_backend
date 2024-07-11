# REST Framework imports
from functools import partial
from rest_framework.decorators import APIView
# Models
from apps.client.models import Request, Client
# Serializers
from apps.client.api.serializers.index import RequestSerializer
# Utils
from apps.base.utils.index import response, sendEmail
# Decorators
from apps.base.decorators.index import checkRole

class RequestAV(APIView):

    @checkRole(['admin'])
    def get(self, request, pk=None):
        try:
            if pk:
                request    = Request.objects.get(id=pk)
                serializer = RequestSerializer(request)
                return response({'error': False, 'data': serializer.data}, 200)
            else:
                request    = Request.objects.filter(state=1)
                serializer = RequestSerializer(request, many=True)
                return response({'error': False, 'data': serializer.data}, 200)
        except Request.DoesNotExist:
            return response({'error': True, 'message': 'Solicitud/es no encontrada'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)


    @checkRole(['admin'])
    def post(self, request):
        try:
            clientRequest = RequestSerializer(data=request.data, context={'request':request})
            if clientRequest.is_valid():
                clientRequest.save()
                return response({'error': False, 'data': clientRequest.data}, 200)
            else:
                return response({'error': True, 'message': clientRequest.errors}, 400)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, 400)

    @checkRole(['admin'])
    def patch(self, request, pk=None):
        try:
            clientRequest = Request.objects.get(id=pk)
            request.data['attended_by'] = request.user.id
            clientRequestSerializer = RequestSerializer(clientRequest, data=request.data, context={'request':request}, partial=True)

            if clientRequestSerializer.is_valid():
                clientRequestSerializer.save()
                client = Client.objects.get(id=clientRequest.client.id)
                
                if request.data['status'] == 1:
                    client.state = 1
                    client.save()
                    sendEmail('solicitud aprobada', 'su solicitud ha sido aprobada',client.email)
                elif request.data['status'] == 2:
                    sendEmail('solicitud rechazada', 'su solicitud ha sido rechazada',client.email)
                return response({'error': False, 'data': clientRequestSerializer.data}, 200)

            else:
                return response({'error': True, 'message': clientRequestSerializer.errors}, 400)

        except Request.DoesNotExist:
            return response({'error': True, 'message': 'Solicitud no encontrada'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, 400)
    
    @checkRole(['admin'])
    def delete(self, request, pk=None):
        try:
            clientRequest = Request.objects.get(id=pk)
            clientRequest.state = 0
            clientRequest.save()
            return response({'error': False, 'message': 'Solicitud eliminada'}, 200)
        except Request.DoesNotExist:
            return response({'error': True, 'message': 'Solicitud no encontrada'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, 400)