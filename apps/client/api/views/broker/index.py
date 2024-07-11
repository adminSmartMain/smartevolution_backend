# REST Framework imports
from django.db.models import Q
# Models
from apps.client.models import Broker, Client
# Serializers
from apps.client.api.serializers.index import BrokerSerializer
# Utils
from apps.base.utils.index import response, BaseAV
# Decorators
from apps.base.decorators.index import checkRole


class BrokerAV(BaseAV):

    @checkRole(['admin'])
    def get(self, request, pk=None):
        try:
            if len(request.query_params) > 0:
                if request.query_params.get('broker') != None:
                    brokers = Broker.objects.filter(Q(first_name__icontains=request.query_params.get('broker'))|
                                                    Q(last_name__icontains=request.query_params.get('broker'))|
                                                    Q(social_reason__icontains=request.query_params.get('broker'))).filter(state=1)
                elif request.query_params.get('document') != None:
                    brokers = Broker.objects.filter(document_number__icontains=request.query_params.get('document')).filter(state=1)
                
                else:
                    brokers = Broker.objects.filter(state=1) 
                page       = self.paginate_queryset(brokers)
                if page is not None:
                    serializer = BrokerSerializer(page, many=True)
                    return self.get_paginated_response(serializer.data)


            if pk == 'all':
                brokers    = Broker.objects.filter(state=1)
                serializer = BrokerSerializer(brokers, many=True)
                return response({'error': False, 'brokers': serializer.data}, 200)

            if pk:
                broker = Broker.objects.get(id=pk)
                serializer = BrokerSerializer(broker)
                return response({'error': False, 'data': serializer.data}, 200)
            else:
                brokers = Broker.objects.filter(state=1)
                page       = self.paginate_queryset(brokers)
                if page is not None:
                    serializer = BrokerSerializer(page, many=True)
                    return self.get_paginated_response(serializer.data)
        except Broker.DoesNotExist:
            return response({'error': True, 'message': 'Corredor/es no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['admin'])
    def post(self, request):
        try:
            serializer = BrokerSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'message': 'Corredor creado', 'data': serializer.data}, 200)
            return response({'error': True, 'message': serializer.errors}, 400)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['admin'])
    def patch(self, request, pk):
        try:
            broker = Broker.objects.get(id=pk)
            serializer = BrokerSerializer(broker, data=request.data, context={
                                          'request': request}, partial=True)
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'message': 'Corredor actualizado', 'data': serializer.data}, 200)
            return response({'error': True, 'message': serializer.errors}, 400)
        except Broker.DoesNotExist:
            return response({'error': True, 'message': 'Corredor no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['admin'])
    def delete(self, request, pk):
        try:
            broker = Broker.objects.get(id=pk)
            broker.state = 0
            broker.save()
            return response({'error': False, 'message': 'Corredor eliminado'}, 200)
        except Broker.DoesNotExist:
            return response({'error': True, 'message': 'Corredor no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)


class BrokerByClientAV(BaseAV):

    @checkRole(['admin', 'client'])
    def get(self, request, pk):
        try:
            # Get client
            client = Client.objects.get(id=pk)
            # Get broker
            broker = Broker.objects.get(id=client.broker.id)
            # Serialize broker
            serializer = BrokerSerializer(broker)
            return response({'error': False, 'data': serializer.data}, 200)
        except Broker.DoesNotExist:
            return response({'error': True, 'message': 'Corredor/es no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
