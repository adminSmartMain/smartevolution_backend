from django.db.models import Q
# REST Framework imports
from apps.base.utils.index import BaseAV
# Models
from apps.administration.models import Refund
# Serializers
from apps.administration.api.serializers.index import RefundSerializer, RefundReadOnlySerializer
# Utils
from apps.base.utils.index import response
# Decorators
from apps.base.decorators.index import checkRole


class RefundAV(BaseAV):

    @checkRole(['admin'])
    def get(self, request, pk=None):
        try:
            if pk:
                refund     = Refund.objects.get(pk=pk)
                serializer = RefundReadOnlySerializer(refund)
                return response({'error': False, 'data': serializer.data}, 200)
            
            if len(request.query_params) > 0:

                if request.query_params.get('id'):
                    refunds   = Refund.objects.filter(rId__icontains=request.query_params.get('id')).filter(state=True)
                elif request.query_params.get('date'):
                    #parse date from dd/mm/yyyy to yyyy-mm-dd
                    date = request.query_params.get('date').split('/')
                    date = date[2] + '-' + date[1] + '-' + date[0]
                    refunds   = Refund.objects.filter(date=date).filter(state=True)
                elif request.query_params.get('client'):
                    refunds = Refund.objects.filter(Q(client__first_name__icontains=request.query_params.get('client')) |
                    Q(client__last_name__icontains=request.query_params.get('client'))
                    | Q(client__social_reason__icontains=request.query_params.get('client'))).filter(state=True)
                elif request.query_params.get('beneficiary'):
                    refunds = Refund.objects.filter(Q(beneficiary__icontains=request.query_params.get('beneficiary'))).filter(state=True)
                else:
                    refunds   = Refund.objects.filter(state=True)

                page       = self.paginate_queryset(refunds)
                if page is not None:
                    serializer = RefundReadOnlySerializer(page, many=True)
                    return self.get_paginated_response(serializer.data)
        except Refund.DoesNotExist:
            return response({'error': True, 'message': 'Reintegro/s no encontrados'}, 500)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
    @checkRole(['admin'])
    def post(self, request):
        try:
            serializer = RefundSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'message': 'Reintegro creado', 'data': serializer.data}, 200)
            return response({'error': True, 'message': serializer.errors}, 400)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
    @checkRole(['admin'])
    def patch(self, request, pk):
        try:
            refund     = Refund.objects.get(pk=pk)
            serializer = RefundSerializer(refund, data=request.data, context={'request': request}, partial=True)
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'message': 'Reintegro actualizado', 'data': serializer.data}, 200)
            return response({'error': True, 'message': serializer.errors}, 400)
        except Refund.DoesNotExist:
            return response({'error': True, 'message': 'Reintegro no encontrado'}, 500)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['admin'])
    def delete(self, request, pk):
        try:
            refund = Refund.objects.get(pk=pk)
            # add amount to account
            refund.account.balance += (refund.amount + refund.gmAmount)
            refund.account.save()
            refund.state = False
            refund.save()
            # then delete the refund 
            refund.delete()
            return response({'error': False, 'message': 'Reintegro eliminado'}, 200)
        except Refund.DoesNotExist:
            return response({'error': True, 'message': 'Reintegro no encontrado'}, 500)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
