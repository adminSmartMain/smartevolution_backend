# REST Framework imports
from rest_framework.decorators import APIView
# Models
from apps.client.models import RiskProfile, Client
# Serializers
from apps.client.api.serializers.index import RiskProfileSerializer, RiskProfileReadOnlySerializer
# Utils
from apps.base.utils.index import response
# Decorators
from apps.base.decorators.index import checkRole


class RiskProfileAV(APIView):
    
    @checkRole(['admin'])
    def get(self, request, pk=None):
        if pk:
            riskProfile = RiskProfile.objects.get(pk=pk)
            serializer  = RiskProfileSerializer(riskProfile)
            return response({'error': False, 'data': serializer.data}, 200)
        else:
            riskProfile = RiskProfile.objects.filter(state=1)
            serializer  = RiskProfileSerializer(riskProfile, many=True)
            return response({'error': False, 'data': serializer.data}, 200)

    @checkRole(['admin'])
    def post(self, request):
        serializer = RiskProfileSerializer(data=request.data, context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return response({'error': False, 'data': serializer.data}, 200)
        else:
            return response({'error': True, 'message': serializer.errors}, 400)
    
    @checkRole(['admin'])
    def patch(self, request, pk=None):
        riskProfile = RiskProfile.objects.get(id=pk)
        serializer  = RiskProfileSerializer(riskProfile, data=request.data, context={'request':request}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return response({'error': False, 'data': serializer.data}, 200)
        else:
            return response({'error': True, 'message': serializer.errors}, 400)

    @checkRole(['admin'])
    def delete(self, request, pk=None):
        riskProfile = RiskProfile.objects.get(id=pk)
        riskProfile.state = 0
        riskProfile.save()
        return response({'error': False, 'message': 'perfil de riesgo eliminado'}, 200)


class RiskProfileByClientAV(APIView):
    
    @checkRole(['admin'])
    def get(self, request, pk=None):
        try:
            if pk:
                riskProfile = RiskProfile.objects.get(client=pk)
                serializer  = RiskProfileReadOnlySerializer(riskProfile)
                return response({'error': False, 'data': serializer.data}, 200)
            else:
                riskProfile = RiskProfile.objects.filter(state=1)
                serializer  = RiskProfileReadOnlySerializer(riskProfile, many=True)
                return response({'error': False, 'data': 'cliente no proveído'}, 200)
        except RiskProfile.DoesNotExist:
            client = Client.objects.get(pk=pk)
            return response({'error': True, 'message':{
                'msg': 'No se ha encontrado un perfil de riesgo para el cliente',
                'client': client.social_reason if client.social_reason else client.first_name + ' ' + client.last_name
            }}, 400)