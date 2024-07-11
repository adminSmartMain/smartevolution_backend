# Django
from django.db.models import Q
# Models
from apps.client.models import Account
# Serializers
from apps.client.api.serializers.index import AccountSerializer, AccountReadOnlySerializer
# Utils
from apps.base.utils.index import response, BaseAV, random_with_N_digits
# Decorators
from apps.base.decorators.index import checkRole


class AccountAV(BaseAV):

    @checkRole(['admin'])
    def get(self, request, pk=None):
        try:
            if len(request.query_params) > 0:
                if request.query_params.get('client') != None:
                    account = Account.objects.filter(Q(client__social_reason__icontains=request.query_params.get('client'))|
                                                     Q(client__first_name__icontains=request.query_params.get('client'))|
                                                     Q(client__last_name__icontains=request.query_params.get('client')))
                    page = self.paginate_queryset(account)
                    if page is not None:
                        serializer = AccountReadOnlySerializer(page, many=True)
                        return self.get_paginated_response(serializer.data)
            if pk:
                account = Account.objects.get(id=pk)
                serializer = AccountReadOnlySerializer(account)
                return response({'error': False, 'data': serializer.data}, 200)
            else:
                accounts = Account.objects.all()
                page = self.paginate_queryset(accounts)
                if page is not None:
                    serializer = AccountReadOnlySerializer(page, many=True)
                    return self.get_paginated_response(serializer.data)
        except Account.DoesNotExist:
            return response({'error': True, 'message': 'Cuenta/s no encontradas'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
        
    @checkRole(['admin'])
    def post(self, request):
        try:
            request.data['account_number'] = random_with_N_digits(10)
            serializer = AccountSerializer(data=request.data, context={'request':request})
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'message': 'Cuenta creada', 'data':serializer.data}, 200)
            return response({'error': True, 'message': serializer.errors}, 400)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
    @checkRole(['admin'])
    def patch(self, request, pk):
        try:
            account     = Account.objects.get(id=pk)
            serializer  = AccountSerializer(account, data=request.data, context={'request':request}, partial=True)
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'message': 'Cuenta actualizada','data':serializer.data}, 200)
            return response({'error': True, 'message': serializer.errors}, 400)
        except Account.DoesNotExist:
            return response({'error': True, 'message': 'Cuenta no encontrada'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
    @checkRole(['admin'])
    def delete(self, request, pk):
        try:
            account = Account.objects.get(id=pk)
            account.state = False
            account.save()
            return response({'error': False, 'message': 'Cuenta deshabilitada'}, 200)
        except Account.DoesNotExist:
            return response({'error': True, 'message': 'Cuenta no encontrada'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)



class AccountByClientAV(BaseAV):

    @checkRole(['admin'])
    def get(self, request, pk=None):
        try:
            accounts = Account.objects.filter(client=pk)
            serializer = AccountSerializer(accounts, many=True)
            if len(accounts) == 0:
                return response({'error': True, 'message': 'Cuenta/s no encontradas'}, 404)
            return response({'error': False, 'data': serializer.data}, 200)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)