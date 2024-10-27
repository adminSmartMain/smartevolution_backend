from django.db.models import Q
# Models
from apps.administration.models import EmitterDeposit, AccountingControl
# Serializers
from apps.administration.api.serializers.index import EmitterDepositSerializer, EmitterDepositReadOnlySerializer, EmitterDepositNSSerializer
# Utils
from apps.base.utils.index import response, BaseAV
# Decorators
from apps.base.decorators.index import checkRole


class EmitterDepositAV(BaseAV):

    @checkRole(['admin'])
    def get(self, request, pk=None):
        try:
            if pk:
                emitterDeposit = EmitterDeposit.objects.get(pk=pk)
                serializer = EmitterDepositReadOnlySerializer(emitterDeposit)
                return response({'error': False, 'data': serializer.data}, 200)

            if len(request.query_params) > 0:
                if request.query_params.get('emitter') != None:

                    EmitterDeposits   = EmitterDeposit.objects.filter(Q(client__first_name__icontains=request.query_params.get('emitter')) |
                                                        Q(client__last_name__icontains=request.query_params.get('emitter')) |
                                                        Q(client__social_reason__icontains=request.query_params.get('emitter'))).filter(state=1)
                elif request.query_params.get('id') != None:
                    EmitterDeposits   = EmitterDeposit.objects.filter(edId__icontains=request.query_params.get('id')).filter(state=1)
                elif request.query_params.get('date') != None:
                    #parse date from dd/mm/yyyy to yyyy-mm-dd
                    date = request.query_params.get('date').split('/')
                    date = date[2] + '-' + date[1] + '-' + date[0]
                    EmitterDeposits   = EmitterDeposit.objects.filter(date=date).filter(state=1)
                elif request.query_params.get('opId') != None:
                    emitterDeposits = EmitterDeposit.objects.filter(operation__opId=request.query_params.get('opId')).filter(state=1)
                    serializer = EmitterDepositNSSerializer(emitterDeposits, many=True)
                    return response({'error': False, 'data': serializer.data}, 200)

                    
                else:
                    EmitterDeposits   = EmitterDeposit.objects.filter(state=1)

                page       = self.paginate_queryset(EmitterDeposits)
                if page is not None:
                    serializer = EmitterDepositReadOnlySerializer(page, many=True)
                    return self.get_paginated_response(serializer.data)

            

        except EmitterDeposit.DoesNotExist:
            return response({'error': True, 'message': 'Giro/s no encontrados'}, 500)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
    @checkRole(['admin'])
    def post(self, request):
        try:
            serializer = EmitterDepositSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'message': 'Giro creado', 'data': serializer.data}, 200)
            return response({'error': True, 'message': serializer.errors}, 400)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['admin'])
    def patch(self, request, pk):
        try:
            emitterDeposit = EmitterDeposit.objects.get(pk=pk)
            serializer     = EmitterDepositSerializer(emitterDeposit, data=request.data, context={'request': request}, partial=True)
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'message': 'Giro actualizado', 'data': serializer.data}, 200)
            return response({'error': True, 'message': serializer.errors}, 400)
        except EmitterDeposit.DoesNotExist:
            return response({'error': True, 'message': 'giro no encontrado'}, 500)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['admin'])
    def delete(self, request, pk):
        try:
            emitterDeposit = EmitterDeposit.objects.get(pk=pk)
            # delete the accounting control for the deposit
            try:
                AccountingControl.objects.get(emitterDeposit_id=emitterDeposit.id).delete()
            except AccountingControl.DoesNotExist:
                pass
            # set the state to false
            emitterDeposit.state = False # esto no elimina, solo pasa a 0
            emitterDeposit.save()
            return response({'error': False, 'message': 'giro eliminado'}, 200)
        except EmitterDeposit.DoesNotExist:
            return response({'error': True, 'message': 'giro no encontrado'}, 500)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
