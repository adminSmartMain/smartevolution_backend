from django.db.models import Q
# Models
from apps.administration.models import Deposit
# Serializers
from apps.administration.api.serializers.index import DepositSerializer, DepositReadOnlySerializer
# Utils
from apps.base.utils.index import response, BaseAV
# Decorators
from apps.base.decorators.index import checkRole


class DepositAV(BaseAV):

    @checkRole(['admin'])
    def get(self, request, pk=None):
        try:

            if pk:
                if pk != 'all':
                    deposit    = Deposit.objects.get(pk=pk)
                    serializer = DepositReadOnlySerializer(deposit)
                    return response({'error': False, 'data': serializer.data}, 200)
                else:
                    deposits   = Deposit.objects.filter(state=1)
                    serializer = DepositReadOnlySerializer(deposits, many=True)
                    return response({'error': False, 'data': serializer.data}, 200)

            if len(request.query_params) > 0:
                if request.query_params.get('investor'):
                    deposits   = Deposit.objects.filter(Q(client__first_name__icontains=request.query_params.get('investor')) |
                                                        Q(client__last_name__icontains=request.query_params.get('investor')) |
                                                        Q(client__social_reason__icontains=request.query_params.get('investor'))).filter(state=1)
                elif request.query_params.get('id'):
                    deposits   = Deposit.objects.filter(dId=request.query_params.get('id')).filter(state=1)
                elif request.query_params.get('date'):
                    date = request.query_params.get('date').split('/')
                    date = date[2] + '-' + date[1] + '-' + date[0]
                    deposits   = Deposit.objects.filter(date=date).filter(state=1)
                else:
                    deposits   = Deposit.objects.filter(state=1)

                page       = self.paginate_queryset(deposits)
                if page is not None:
                    serializer = DepositReadOnlySerializer(page, many=True)
                    return self.get_paginated_response(serializer.data)

        except Deposit.DoesNotExist:
            return response({'error': True, 'message': 'Giro/s no encontrados'}, 500)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
    @checkRole(['admin'])
    def post(self, request):
        try:
            serializer = DepositSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'message': 'Giro creado', 'data': serializer.data}, 200)
            return response({'error': True, 'message': serializer.errors}, 400)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
    @checkRole(['admin'])
    def patch(self, request, pk):
        try:
            deposit    = Deposit.objects.get(pk=pk)
            serializer = DepositSerializer(deposit, data=request.data, context={'request': request}, partial=True)
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'message': 'Giro actualizado', 'data': serializer.data}, 200)
            return response({'error': True, 'message': serializer.errors}, 400)
        except Deposit.DoesNotExist:
            return response({'error': True, 'message': 'giro no encontrado'}, 500)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['admin'])
    def delete(self, request, pk):
        try:
            deposit = Deposit.objects.get(pk=pk)
            deposit.state = 0
            deposit.account.balance -= deposit.amount
            deposit.account.save()
            deposit.save()
            return response({'error': False, 'message': 'giro eliminado'}, 200)
        except Deposit.DoesNotExist:
            return response({'error': True, 'message': 'giro no encontrado'}, 500)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)