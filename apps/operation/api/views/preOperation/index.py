# REST Framework imports
from rest_framework.decorators import APIView
from django.db.models import Q, Count
# Models
from apps.client.models import Client, RiskProfile, Account, Broker
from apps.operation.models import PreOperation, Receipt, BuyOrder
from apps.bill.models import Bill
from apps.misc.models import TypeBill
# Serializers
from apps.operation.api.serializers.index import (PreOperationSerializer, PreOperationReadOnlySerializer, 
                                                  ReceiptSerializer, PreOperationSignatureSerializer, PreOperationByParamsSerializer)
# Utils
from apps.base.utils.index import response, gen_uuid, BaseAV
from apps.report.utils.index import generateSellOffer, calcOperationDetail
import pandas as pd
import json
from time import strftime, localtime
from functools import reduce
# Decorators
from apps.base.decorators.index import checkRole
#utils
from apps.base.utils.logBalanceAccount import log_balance_change
import logging

# Configurar el logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Crear un handler de consola y definir el nivel
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Crear un formato para los mensajes de log
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Añadir el handler al logger
logger.addHandler(console_handler)


class PreOperationAV(BaseAV):

    @checkRole(['admin'])
    def post(self, request):
        try:
            if request.data['billCode'] != '':
                emitter  = Client.objects.get(pk=request.data['emitter'])
                payer    = Client.objects.get(pk=request.data['payer'])
                typeBill = TypeBill.objects.get(pk='fdb5feb4-24e9-41fc-9689-31aff60b76c9')
                bill     = Bill.objects.create(
                    id=gen_uuid(),
                    typeBill=typeBill,
                    billId=request.data['billCode'],
                    emitterId=emitter.document_number,
                    emitterName=emitter.social_reason if emitter.social_reason else emitter.first_name + ' ' + emitter.last_name,
                    payerId=payer.document_number,
                    payerName=payer.social_reason if payer.social_reason else payer.first_name + ' ' + payer.last_name,
                    billValue = request.data['amount'],
                    subTotal = request.data['amount'],
                    total = request.data['amount'],
                    currentBalance = request.data['amount'],
                    dateBill = request.data['DateBill'],
                    datePayment = request.data['DateExpiration'],
                    expirationDate = request.data['DateExpiration'],
                    )
                bill.save()
                request.data['bill'] = bill.id
            serializer = PreOperationSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'message': 'operación creada','data': serializer.data}, 200)
            return response({'error': True, 'message': serializer.errors}, 400)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
    @checkRole(['admin'])
    def get(self, request, pk=None):
        logger.debug(f"PreOperationAV")
        logger.debug(request)
        logger.debug(request.query_params)
        logger.debug( len(request.query_params))
        try:

            if pk:
                if len(request.query_params) > 0:
                    try:
                        preOperation  = PreOperation.objects.get(pk=request.query_params.get('id'))
                        
                        serializer    = PreOperationReadOnlySerializer(preOperation)
                        return response({'error': False, 'data': serializer.data}, 200)
                    except Exception as e:
                        return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
                        
                    
                else:
                    
                    preOperation  = PreOperation.objects.get(pk=pk)
                    serializer    = PreOperationReadOnlySerializer(preOperation)
                    receipts      = Receipt.objects.filter(operation=pk).order_by('-date')
                    receipts_data = ReceiptSerializer(receipts, many=True)
                    calcs = {
                        'lastDate': receipts_data.data[0]['date'] if len(receipts_data.data) > 0 else None,
                        'payedAmount': 0,
                        'interest': 0,
                    }
                    for x in receipts_data.data:
                        calcs['payedAmount'] += x['payedAmount']
                        calcs['interest'] += x['additionalInterests']
                    return response({'error': False, 'data': serializer.data, 'receipts':calcs}, 200)

            if len(request.query_params) > 0:
                if (request.query_params.get('opId') != 'undefined') and (request.query_params.get('notifications') == 'electronicSignature'):
                    logger.debug('a')
                    # get the operation data
                    
                    preOperation = PreOperation.objects.filter(opId=request.query_params.get('opId'))
                    serializer   = PreOperationReadOnlySerializer(preOperation, many=True)
                    
                  
                    
                    pendingOperations  = []
                    filteredOperations = []
                    # get the operations who doesn't have a buy order
                    for x in preOperation:
                        if len(BuyOrder.objects.filter(operation_id=x.id)) == 0:
                            pendingOperations.append(x)
                   
                    # group the operations by investor and if a operation is already in the filteredOperations sum the payedAmount to the existing operation
                    n=1
                    for x in pendingOperations:
                        if x.investor not in [y.investor for y in filteredOperations]:
                          
                            filteredOperations.append(x)
                        else:
                           
                            for y in filteredOperations:
                                
                                if x.investor == y.investor and x.opId == y.opId:
                                    y.payedAmount += x.payedAmount
                                    y.presentValueInvestor += x.presentValueInvestor
                                   
                                    if x.investorTax !=0:
                                        y.investorTax =(x.investorTax+y.investorTax)
                                        logger.debug(f" voy en el if de diferente de 0 este es el n {n}")
                                        n=n+1
                                    else:
                                        logger.debug(f" voy en el if de igual a de 0 este es el n {n}") 
                                        y.investorTax =(x.investorTax+y.investorTax)
                                   
                                    logger.debug(f" y.investorTax  de buscar por investor { y.investorTax}")
                                    break
                                elif x.investor == y.investor and x.opId != y.opId:
                                    filteredOperations.append(x)
                                    break
                                
                                
                   
                    if x.investorTax:
                        y.investorTax=round(y.investorTax/n,2)
                    
                    page = self.paginate_queryset(filteredOperations)
                    if page is not None:
                        serializer   = PreOperationSignatureSerializer(page, many=True)
                        return self.get_paginated_response(serializer.data)
                   
                
                elif (request.query_params.get('opId') != 'undefined') and (len(request.query_params)==1):
                    
                    data = generateSellOffer(request.query_params.get('opId'))
                    # get the operation data
                    
                    preOperation = PreOperation.objects.filter(opId=request.query_params.get('opId'))
                    serializer   = PreOperationReadOnlySerializer(preOperation, many=True)
                    
                    data['investor']['investorAccount'] = serializer.data[0]['clientAccount']
                    return response({'error': False, 'data': data}, 200)
                elif (request.query_params.get('notifications') == 'new-preoperation') and (request.query_params.get('opId') != 'undefined'):
                   
                    logger.debug('aquii en el if mio')
                    preOperation = PreOperation.objects.filter(opId=request.query_params.get('opId'))
                    
                    # only return one op per opId
                    filteredOperations = []
                    for x in preOperation:
                        if x.opId not in [y.opId for y in filteredOperations]:
                            filteredOperations.append(x)
                    logger.debug(filteredOperations)
                    
                elif request.query_params.get('opIdV') != 'undefined':
                    #ACA SE TOMAN LOS DATOS AL MOMENTO DE PRESIONAR AL WHATSAPP
                    
                    logger.debug(len(request.query_params))
                    data = calcOperationDetail(request.query_params.get('opIdV'), request.query_params.get('investor')) 
                    return response({'error': False, 'data': data}, 200)
                elif request.query_params.get('notifications') == 'electronicSignature' and request.query_params.get('nOpId') == 'undefined':
                    
                    if 'investor' in request.query_params:
                       
                        preOperation = PreOperation.objects.filter(status=0).filter(Q(investor__last_name__icontains=request.query_params.get('investor')) |
                                                            Q(investor__first_name__icontains=request.query_params.get('investor')) |
                                                            Q(investor__social_reason__icontains=request.query_params.get('investor')) )
                    else:
                        preOperation = PreOperation.objects.filter(status=0)
                    
                    pendingOperations  = []
                    filteredOperations = []
                    # get the operations who doesn't have a buy order
                    for x in preOperation:
                        if len(BuyOrder.objects.filter(operation_id=x.id)) == 0:
                            pendingOperations.append(x)
                    
                    # group the operations by investor and if a operation is already in the filteredOperations sum the payedAmount to the existing operation
                    for x in pendingOperations:
                        if x.investor not in [y.investor for y in filteredOperations]:
                            filteredOperations.append(x)
                        else:
                            
                            for y in filteredOperations:
                                if x.investor == y.investor and x.opId == y.opId:
                                    y.payedAmount += x.payedAmount
                                    y.presentValueInvestor += x.presentValueInvestor
                                    
                                   
                                    break
                                elif x.investor == y.investor and x.opId != y.opId:
                                    filteredOperations.append(x)
                                    break
                   
                    page = self.paginate_queryset(filteredOperations)
                    if page is not None:
                        serializer   = PreOperationSignatureSerializer(page, many=True)
                        return self.get_paginated_response(serializer.data)
                elif request.query_params.get('notifications') == 'notifications' and request.query_params.get('nOpId') == 'undefined':
                    logger.debug('b')
                    preOperation = PreOperation.objects.filter(Q(status = 1) | Q(status = 3))
                    # only return one op per opId
                    filteredOperations = []
                    for x in preOperation:
                        if x.opId not in [y.opId for y in filteredOperations]:
                            filteredOperations.append(x)
                    # paginate the queryset
                    page = self.paginate_queryset(filteredOperations)
                    if page is not None:
                        serializer   = PreOperationSignatureSerializer(page, many=True)
                        return self.get_paginated_response(serializer.data)
               
                
                elif request.query_params.get('notifications') != 'undefined' and request.query_params.get('nOpId') != 'undefined':
                    preOperation = PreOperation.objects.filter(Q(status = 1) | Q(status = 3)).filter(opId=request.query_params.get('nOpId'))
                # paginate the queryset
                page = self.paginate_queryset(preOperation)
                if page is not None:
                    serializer   = PreOperationSignatureSerializer(preOperation, many=True)
                    return self.get_paginated_response(serializer.data)                  


            else:
                preOperations = PreOperation.objects.filter(state=1)
                serializer    = PreOperationReadOnlySerializer(preOperations, many=True)
                return response({'error': False, 'data': serializer.data}, 200)
        except PreOperation.DoesNotExist:
            return response({'error': True, 'message': 'operacion/es no encontradas'}, 500)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
    @checkRole(['admin'])
    def patch(self, request, pk):
        try:
            if request.data['billCode'] != '':
                emitter = Client.objects.get(pk=request.data['emitter'])
                payer = Client.objects.get(pk=request.data['payer'])
                typeBill = TypeBill.objects.get(pk='a7c70741-8c1a-4485-8ed4-5297e54a978a')
                bill = Bill.objects.create(
                    id=gen_uuid(),
                    typeBill=typeBill,
                    billId=request.data['billCode'],
                    emitterId=emitter.document_number,
                    emitterName=emitter.social_reason if emitter.social_reason else emitter.first_name + ' ' + emitter.last_name,
                    payerId=payer.document_number,
                    payerName=payer.social_reason if payer.social_reason else payer.first_name + ' ' + payer.last_name,
                    billValue = request.data['amount'],
                    subTotal = request.data['amount'],
                    total = request.data['amount'],
                    currentBalance = request.data['amount'],
                    dateBill = request.data['DateBill'],
                    datePayment = request.data['DateExpiration'],
                    expirationDate = request.data['DateExpiration'],
                    )
                bill.save()
                request.data['bill'] = bill.id
            
            # check if massive and massiveByInvestor are in the request data
            if 'massive' not in request.data and 'massiveByInvestor' not in request.data:
                preOperation = PreOperation.objects.get(pk=pk)
                serializer   = PreOperationSerializer(preOperation, data=request.data, context={'request': request}, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return response({'error': False, 'data': serializer.data}, 200)
                else:
                    return response({'error': True, 'message': serializer.errors}, 500)
            elif request.data['massive'] == True:
                preOperation = PreOperation.objects.get(pk=pk)
                if request.data['status'] == 2:
                    # get the operations with the same opId
                    operations = PreOperation.objects.filter(opId=preOperation.opId, investor=preOperation.investor)
                    for operation in operations:
                        operation.status = 2
                        operation.bill.currentBalance += operation.payedAmount

                        log_balance_change(operation.clientAccount, operation.clientAccount.balance, (operation.clientAccount.balance + operation.presentValueInvestor), operation.presentValueInvestor, 'pre_operation', operation.id, 'PreOperation View - patch')
                        operation.clientAccount.balance += operation.presentValueInvestor
                        log_balance_change(operation.clientAccount, operation.clientAccount.balance, (operation.clientAccount.balance + operation.GM), operation.GM, 'pre_operation', operation.id, 'PreOperation View - patch 2')
                        operation.clientAccount.balance += operation.GM
                        operation.bill.save()
                        operation.clientAccount.save()
                        operation.save()
                    return response({'error': False, 'message': 'Operaciones Actualizada'}, 200)
                else:
                    # get the operations with the same opId
                    operations = PreOperation.objects.filter(opId=preOperation.opId, investor=preOperation.investor)
                    for operation in operations:
                        if operation.status == 0 and operation.status != 1:
                            operation.status = 1

                            log_balance_change(operation.clientAccount, operation.clientAccount.balance, (operation.clientAccount.balance - (operation.presentValueInvestor + operation.GM)), -(operation.presentValueInvestor + operation.GM), 'pre_operation', operation.id, 'PreOperation View - patch 3')
                            operation.clientAccount.balance -= (operation.presentValueInvestor + operation.GM)
                            operation.clientAccount.save()
                            operation.save()
                    return response({'error': False, 'message': 'Operaciones Actualizada'}, 200)
            elif request.data['massiveByInvestor'] == True:
                preOperation = PreOperation.objects.filter(opId=request.data['opId'], investor=request.data['investor'])
                for operations in preOperation:
                    if request.data['status'] == 2:
                        operations.status = 2
                        operations.bill.currentBalance += operations.payedAmount
                        
                        log_balance_change(operations.clientAccount, operations.clientAccount.balance, (operations.clientAccount.balance + operations.presentValueInvestor), operations.presentValueInvestor, 'pre_operation', operations.id, 'PreOperation View - patch 4')
                        operations.clientAccount.balance += operations.presentValueInvestor

                        log_balance_change(operations.clientAccount, operations.clientAccount.balance, (operations.clientAccount.balance + operations.operations.GM), operations.operations.GM, 'pre_operation', operations.id, 'PreOperation View - patch 5')
                        operations.clientAccount.balance += operations.GM
                        operations.clientAccount.save()
                        operations.bill.save()
                        operations.save()
                        return response({'error': False, 'message': 'Operaciones Actualizada'}, 200)
                    elif request.data['status'] == 1:
                        if operations.status == 0 and operations.status != 1:
                            operations.status = 1

                            log_balance_change(operations.clientAccount, operations.clientAccount.balance, (operations.clientAccount.balance - (operations.presentValueInvestor + operations.GM)), -(operations.presentValueInvestor + operations.GM), 'pre_operation', operations.id, 'PreOperation View - patch 6')
                            operations.clientAccount.balance -= (operations.presentValueInvestor + operations.GM)
                            operations.clientAccount.save()
                            operations.save()
                        return response({'error': False, 'message': 'Operaciones Actualizada'}, 200)

                if request.data['status'] == 1:
                    # get the operations with the same opId
                    operations = PreOperation.objects.filter(opId=preOperation.opId)
                    for operation in operations:
                        operation.status = 1
                        operation.save()    



                return response({'error': False, 'message': 'Operaciones Actualizada'}, 200)

            else:     
                preOperation = PreOperation.objects.get(pk=pk)
                serializer   = PreOperationSerializer(preOperation, data=request.data, context={'request': request}, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return response({'error': False, 'message': 'Operacion Actualizada', 'data': serializer.data}, 200)
            return response({'error': True, 'message': serializer.errors}, 400)
        except PreOperation.DoesNotExist:
            return response({'error': True, 'message': 'Operacion no encontrada'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['admin'])
    def delete(self, request, pk):
        try:
            preOperation       = PreOperation.objects.get(id=pk)
            # return the balance to the client
            preOperation.bill.currentBalance   += preOperation.payedAmount
            #preOperation.clientAccount.balance += preOperation.payedAmount
            preOperation.bill.save()
            #preOperation.clientAccount.save()
            preOperation.delete()
            return response({'error': False, 'message': 'operacion eliminada'}, 200)
        except PreOperation.DoesNotExist:
            return response({'error': True, 'message': 'operacion no encontrada'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)



class GetLastOperationAV(APIView):
    def get(self, request):
        logger.debug(f" GetLastOperationAV")
        try:
            preOperations = PreOperation.objects.all().order_by('-opId').first()
            serializer    = PreOperationSerializer(preOperations)
            if len(serializer.data) > 0:
                return response({'error': False, 'data': serializer.data['opId'] + 1}, 200)
            return response({'error': False, 'data': 1}, 200)
        except PreOperation.DoesNotExist:
            return response({'error': True, 'message': 'operacion no encontrada'}, 500)
        except Exception as e:
            if str(e) == "unsupported operand type(s) for +: 'NoneType' and 'int'":
                return response({'error': False, 'data': 1}, 200)
                
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)


class GetBillFractionAV(APIView):
    def get(self, request, pk):
        logger.debug(f"GetBillFractionAV")
        try:
            # detect if a bill in operation has previously been fractioned and get the last fraction using bill id
            preOperations = PreOperation.objects.filter(bill=pk).order_by('-opId').first()
            serializer    = PreOperationSerializer(preOperations)
            if (len(serializer.data) > 0 and serializer.data['bill'] != None):
                    return response({'error': False, 'data': {
                        'fraction' : serializer.data['billFraction'] + 1,
                        'billValue': preOperations.bill.currentBalance,
                        'dateBill' : preOperations.bill.dateBill,
                        'datePayment': preOperations.bill.datePayment,
                        'expirationDate'    : preOperations.bill.expirationDate,
                    }}, 200)
            # if the bill has not been fractioned before, get the bill data using bill id
            bill = Bill.objects.get(pk=pk)
            return response({'error': False, 'data': {
                'fraction' : 0,
                'billValue': bill.currentBalance,
                'dateBill' : bill.dateBill,
                'datePayment': bill.datePayment,
                'expirationDate'    : bill.expirationDate,
            }}, 200)            
        except PreOperation.DoesNotExist:
            return response({'error': True, 'message': 'operacion no encontrada'}, 500)
        except Exception as e:
            if str(e) == "unsupported operand type(s) for +: 'NoneType' and 'int'":
                bill = Bill.objects.get(pk=pk)
                return response({'error': False, 'data': {
                        'fraction' : 0,
                        'billValue': bill.currentBalance,
                        'dateBill' : bill.dateBill,
                        'datePayment': bill.datePayment,
                        'expirationDate'    : bill.expirationDate,
                    }}, 200)    
                
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)



class GetOperationByEmitter(APIView):
    def get(self, request, pk):
        logger.debug(f"GetOperationByEmitter")
        try:
            preOperations = PreOperation.objects.filter(emitter=pk)
            serializer    = PreOperationSerializer(preOperations, many=True)
            return response({'error': False, 'data': serializer.data}, 200)
        except PreOperation.DoesNotExist:
            return response({'error': True, 'message': 'operacion no encontrada'}, 500)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)


class GetOperationByParams(BaseAV):
    def get(self, request):
        logger.debug(f"GetOperationByParams")
        try:
            if (request.query_params.get('opId') != '' and request.query_params.get('billId') != '' 
                and request.query_params.get('investor') != ''):
                preOperations = PreOperation.objects.filter(opId=request.query_params.get('opId'),  
                                                            bill_id__billId__icontains=request.query_params.get('billId'),
                                                            ).filter(Q(investor__last_name__icontains=request.query_params.get('investor')) |
                                                            Q(investor__first_name__icontains=request.query_params.get('investor')) |
                                                            Q(investor__social_reason__icontains=request.query_params.get('investor')) |
                                                            Q(emitter__last_name__icontains=request.query_params.get('investor')) |
                                                            Q(emitter__first_name__icontains=request.query_params.get('investor')) |
                                                            Q(emitter__social_reason__icontains=request.query_params.get('investor')))

            elif (request.query_params.get('opId') != '' and request.query_params.get('billId') != '' and request.query_params.get('investor') == ''):
                preOperations = PreOperation.objects.filter(opId=request.query_params.get('opId'),
                                                            bill_id__billId__icontains=request.query_params.get('billId'))

            elif (request.query_params.get('opId') != '' and request.query_params.get('investor') != '' and request.query_params.get('billId') == ''):
                preOperations = PreOperation.objects.filter(opId=request.query_params.get('opId')).filter(Q(investor__last_name__icontains=request.query_params.get('investor')) |
                                                            Q(investor__first_name__icontains=request.query_params.get('investor')) |
                                                            Q(investor__social_reason__icontains=request.query_params.get('investor')) |
                                                            Q(emitter__last_name__icontains=request.query_params.get('investor')) |
                                                            Q(emitter__first_name__icontains=request.query_params.get('investor')) |
                                                            Q(emitter__social_reason__icontains=request.query_params.get('investor'))
            )

            elif (request.query_params.get('billId') != '' and request.query_params.get('investor') != '' and request.query_params.get('opId') == ''):
                preOperations = PreOperation.objects.filter(bill_id__billId__icontains=request.query_params.get('billId')).filter(Q(investor__last_name__icontains=request.query_params.get('investor')) |
                                                            Q(investor__first_name__icontains=request.query_params.get('investor')) |
                                                            Q(investor__social_reason__icontains=request.query_params.get('investor')) |
                                                            Q(emitter__last_name__icontains=request.query_params.get('investor')) |
                                                            Q(emitter__first_name__icontains=request.query_params.get('investor')) |
                                                            Q(emitter__social_reason__icontains=request.query_params.get('investor'))
)

            elif (request.query_params.get('opId') != '' and request.query_params.get('billId') == '' and request.query_params.get('investor') == ''):
                preOperations = PreOperation.objects.filter(opId=request.query_params.get('opId'))


            elif (request.query_params.get('opId') == '' and request.query_params.get('billId') != '' and request.query_params.get('investor') == ''):                
                preOperations = PreOperation.objects.filter(bill_id__billId__icontains=request.query_params.get('billId'))

            elif (request.query_params.get('opId') == '' and request.query_params.get('billId') == '' and request.query_params.get('investor') != ''):
                preOperations = PreOperation.objects.filter(Q(investor__last_name__icontains=request.query_params.get('investor')) |
                                                            Q(investor__first_name__icontains=request.query_params.get('investor')) |
                                                            Q(investor__social_reason__icontains=request.query_params.get('investor')) |
                                                            Q(emitter__last_name__icontains=request.query_params.get('investor')) |
                                                            Q(emitter__first_name__icontains=request.query_params.get('investor')) |
                                                            Q(emitter__social_reason__icontains=request.query_params.get('investor')))
            else:
                preOperations = PreOperation.objects.all()

            if (request.query_params.get('mode') != '' and request.query_params.get('mode') != None):
                possibleStatus = [1, 3, 4, 5]
                preOperations = list(filter(lambda x: x.status in possibleStatus, preOperations))
                

            # calc data for table
            data = {
                'commission': 0,
                'iva': 0,
                'rteFte': 0,
                'retIca': 0,
                'retIva': 0,
                'others': 0,
                'investorValue': 0,
                'netFact':0,
                'futureValue': 0,
                'depositValue': 0,
            }
            if len(preOperations) == 0:
                page = self.paginate_queryset(preOperations)
                if page is not None:
                    serializer   = PreOperationByParamsSerializer(page, many=True)
                    return self.get_paginated_response(serializer.data)
            typeClient = preOperations[0].emitter.type_client.id
            try:
                riskProfile = RiskProfile.objects.get(client = preOperations[0].emitter.id)
            except RiskProfile.DoesNotExist:
                riskProfile = None
            # calc commission
            sum = 0
            presentValueInvestor = 0
            futureValue = 0
            for x in preOperations:
                sum += x.commissionSF
                presentValueInvestor += x.presentValueInvestor
                futureValue += x.amount

            if sum >= 165000:
                data['commission'] = sum
            else:
                data['commission'] = 165000
                
            # calc iva
            data['iva'] = data['commission'] * 0.19
            #calc rteFte
            if typeClient == '21cf32d9-522c-43ac-b41c-4dfdf832a7b8':
                data['rteFte'] = data['commission'] * 0.11


            if riskProfile != None:
                #calc retIca
                if riskProfile.ica == True:
                    data['retIca'] = data['commission'] * 0.00966

                #calc retIva
                if riskProfile.iva == True:
                    data['retIva'] = data['iva'] * 0.15

            #calc investorValue
            data['investorValue'] = presentValueInvestor

            #calc netFact
            data['netFact'] = data['commission'] + data['iva'] - data['rteFte'] - data['retIca'] - data['retIva']
            
            #calc futureValue
            data['futureValue'] = futureValue

            # calc depositValue
            data['depositValue'] = data['investorValue'] - (data['netFact'])

            page = self.paginate_queryset(preOperations)
            if page is not None:
                serializer   = PreOperationByParamsSerializer(page, many=True)
                serializer.data[0]['calcs'] = data
                return self.get_paginated_response(serializer.data)
            
        except PreOperation.DoesNotExist:
            return response({'error': True, 'message': 'operacion no encontrada'}, 500)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)


class OperationDetailAV(APIView):
    def get(self, request, pk):
        logger.debug(f"OperationDetailAV")
        try:
            operation  = PreOperation.objects.filter(opId=pk)
            serializer = PreOperationReadOnlySerializer(operation, many=True)
            return response({'error': False, 'data': serializer.data}, 200)
        except PreOperation.DoesNotExist:
            return response({'error': True, 'message': 'operacion no encontrada'}, 500)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)


class MassiveOperations(APIView):
    def post(self, request):
        try:
            if request.query_params.get('document') != None:
                # get the document from the request
                document = request.FILES.get('document')
                # open the file with pandas
                df   = pd.read_excel(document)
                data = pd.DataFrame.to_json(df, orient='records')
                dictData = pd.DataFrame.to_dict(df, orient='records')
                # excel columns parsed with new names
                parsedColumns = {
                    'ID_OP'                  : 'idProvisional',
                    'NRO_OP'                 : 'opIdProvisional',
                    'TIPO_OP2'               : 'opTypeProvisional',
                    'CUFE_FACT_OP'           : 'cufeProvisional',
                    'NOTIFICACION'           : 'notificationProvisional',
                    'ESTATUS'                : 'statusProvisional',
                    'FECHA_ACT'              : 'updateDateProvisional',
                    'Unnamed: 39'            : 'unnamedProvisional',
                    'VAL_TASA_EM'            : 'emissionRateProvisional',
                    'VAL_TASA_INV'           : 'investorRateProvisional',


                    'NRO_OPD'                : 'opId',
                    'FECHA_RAD_OP'           : 'opDate',
                    'GM_OP'                  : 'applyGm',
                    'TIPO_OP'                : 'opType',
                    'NRO_FACT_OP'            : 'billId',
                    'FRAC_FACT_OP'           : 'billFraction',
                    'ID_EMISOR_OP'           : 'emitterId',
                    'NOMBRE_EMISOR_OP'       : 'emitterName',
                    'ID_PAGADOR_OP'          : 'payerId',
                    'NOMBRE_PAGADOR_OP'      : 'payerName',
                    'ID_INVERSIONISTA_OP'    : 'investorId',
                    'NOMBRE_INVERSIONISTA_OP': 'investorName',
                    'CUENTA_INVERSIONISTA_OP': 'investorAccount',
                    'FECHA_EMISION_FACT'     : 'DateBill',
                    'FECHA_VENCIMIENTO'      : 'DateExpiration',
                    'FECHA_PROB_OP'          : 'probableDate',
                    'FECHA_FIN_OP'           : 'opExpiration',
                    'TASA_DESC_OP'           : 'discountTax',
                    'TASA_INV_OP'            : 'investorTax',
                    'VALOR_FUT_FACT_OP'      : 'amount',
                    'PORC_DESC_OP'           : 'payedPercent',
                    'VALOR_NOM_FACT_OP'      : 'payedAmount',
                    'ID_CORR_V_OP'           : 'emitterBrokerId',
                    'NOMBRE_CORR_V_OP'       : 'emitterBrokerName',
                    'ID_CORR_C_OP'           : 'investorBrokerId',
                    'NOMBRE_CORR_C_OP'       : 'investorBrokerName',
                    'DIAS_OP'                : 'operationDays',
                    'VA_PRESENTE_SM'         : 'presentValueSF',
                    'VA_PRESENTE_INV'        : 'presentValueInvestor',
                    'UTILIDAD_INV'           : 'investorProfit',
                    'COMISION_SM'            : 'commissionSF',
                    'GM_VALOR'               : 'GM',
                }
                # parse the json to a list of dictionaries and rename the columns
                data = json.loads(data)
                parsedData = []
                builtData  = []
                for x in data:
                    parsedData.append({parsedColumns[key]: x[key] for key in x.keys()})

                # delete the unnecessary columns
                for x in parsedData:
                    del x['unnamedProvisional']
                    del x['emissionRateProvisional']
                    del x['investorRateProvisional']
                    del x['opIdProvisional']
                    del x['opTypeProvisional']
                    del x['cufeProvisional']
                    del x['notificationProvisional']
                    del x['statusProvisional']
                    del x['updateDateProvisional']
                    del x['idProvisional']

                # build the data
                for x in parsedData:
                    # check if the bill exists
                    bill = Bill.objects.filter(billId=x['billId'])
                    # get the client account
                    clientAccount = Account.objects.filter(account_number=x['investorAccount'])
                    # get the emitter
                    emitter = Client.objects.filter(document_number=x['emitterId'])[0]
                    # get the payer
                    payer = Client.objects.filter(document_number=x['payerId'])[0]
                    # get the investor
                    investor = Client.objects.filter(document_number=x['investorId'])[0]
                    # get the emitter broker
                    emitterBroker = Broker.objects.filter(document_number=x['emitterBrokerId'])[0]
                    # get the investor broker
                    investorBroker = Broker.objects.filter(document_number=x['investorBrokerId'])[0]


                    if len(bill) > 0:                                      
                        builtData.append({
                            'opId'          :x['opId'],
                            'opDate'        :strftime('%Y-%m-%d', localtime((x['opDate']+ 86400000)/1000)) if x['opDate'] != None else None,
                            'DateBill'      :strftime('%Y-%m-%d', localtime((x['DateBill']+ 86400000)/1000)) if x['DateBill'] != None else None,
                            'DateExpiration':strftime('%Y-%m-%d', localtime((x['DateExpiration']+ 86400000)/1000)) if x['DateExpiration'] != None else None,
                            'probableDate'  :strftime('%Y-%m-%d', localtime((x['probableDate']+ 86400000)/1000)) if x['probableDate'] != None else None,
                            'opExpiration'  :strftime('%Y-%m-%d', localtime((x['opExpiration']+ 86400000)/1000)) if x['opExpiration'] != None else None,
                            'applyGm'       :False if x['applyGm'] == -1 else True,
                            'amount'        :x['amount'],
                            'billCode'      :"",
                            'bill'          :bill[0].id,
                            'billFraction'  :0 if x['billFraction'] == None else x['billFraction'],
                            'clientAccount' :clientAccount[0].id if len(clientAccount) > 0 else 'CUENTA INEXISTENTE',
                            'commissionSF'  :x['commissionSF'],
                            'discountTax'   :round(x['discountTax'] * 100, 2),
                            'investorTax'   :round(x['investorTax'] * 100, 2),
                            'emitter'       :emitter.id,
                            'emitterBroker' :emitterBroker.id,
                            'investor'      :investor.id,
                            'investorBroker':investorBroker.id,
                            'payer'         :payer.id,
                            'investorProfit':x['investorProfit'],
                            'opType'        :'4ba7b2ef-07b1-47bd-8239-e3ce16ea2e94',
                            'operationDays' :x['operationDays'],
                            'payedAmount'   :x['payedAmount'],
                            'payedPercent'  :x['payedPercent'],
                            'presentValueInvestor':x['presentValueInvestor'] * -1,
                            'presentValueSF'      :x['presentValueSF'] * -1,
                            'GM'            :x['GM'],
                        })
                    else:
                        builtData.append({
                            'opId'          :x['opId'],
                            'opDate'        :strftime('%Y-%m-%d', localtime((x['opDate']+ 86400000)/1000)) if x['opDate'] != None else None,
                            'DateBill'      :strftime('%Y-%m-%d', localtime((x['DateBill']+ 86400000)/1000)) if x['DateBill'] != None else None,
                            'DateExpiration':strftime('%Y-%m-%d', localtime((x['DateExpiration']+ 86400000)/1000)) if x['DateExpiration'] != None else None,
                            'probableDate'  :strftime('%Y-%m-%d', localtime((x['probableDate']+ 86400000)/1000)) if x['probableDate'] != None else None,
                            'opExpiration'  :strftime('%Y-%m-%d', localtime((x['opExpiration']+ 86400000)/1000)) if x['opExpiration'] != None else None,
                            'applyGm'       :False if x['applyGm'] == 0 else True,
                            'amount'        :x['amount'],
                            'billCode'      :x['billId'],
                            'billFraction'  :0 if x['billFraction'] == None else x['billFraction'],
                            'clientAccount' :clientAccount[0].id if len(clientAccount) > 0 else 'CUENTA INEXISTENTE',
                            'commissionSF'  :x['commissionSF'],
                            'discountTax'   :round(x['discountTax'] * 100, 2),
                            'investorTax'   :round(x['investorTax'] * 100, 2),
                            'emitter'       :emitter.id,
                            'emitterBroker' :emitterBroker.id,
                            'investor'      :investor.id,
                            'investorBroker':investorBroker.id,
                            'payer'         :payer.id,
                            'investorProfit':x['investorProfit'],
                            'opType'        :'4ba7b2ef-07b1-47bd-8239-e3ce16ea2e94',
                            'operationDays' :x['operationDays'],
                            'payedAmount'   :x['payedAmount'],
                            'payedPercent'  :x['payedPercent'],
                            'presentValueInvestor':x['presentValueInvestor'] * -1,
                            'presentValueSF'      :x['presentValueSF'] * -1,
                            'GM'                  :x['GM'],
                        })
                    
                return response({'error': False, 'data': { 'parsed': builtData, 'raw': data }}, 200)
            else:
                # construct the data for the bulk create
                data = []
                for x in request.data['data']:
                    if x['billCode'] != '':
                        emitter  = Client.objects.get(pk=x['emitter'])
                        payer    = Client.objects.get(pk=x['payer'])
                        typeBill = TypeBill.objects.get(pk='fdb5feb4-24e9-41fc-9689-31aff60b76c9')
                        bill     = Bill.objects.create(
                            id=gen_uuid(),
                            typeBill=typeBill,
                            billId=x['billCode'],
                            emitterId=emitter.document_number,
                            emitterName=emitter.social_reason if emitter.social_reason else emitter.first_name + ' ' + emitter.last_name,
                            payerId=payer.document_number,
                            payerName=payer.social_reason if payer.social_reason else payer.first_name + ' ' + payer.last_name,
                            billValue = x['amount'],
                            subTotal = x['amount'],
                            total = x['amount'],
                            currentBalance = x['amount'],
                            dateBill = x['DateBill'],
                            datePayment = x['DateExpiration'],
                            expirationDate = x['DateExpiration'],
                            )
                        bill.save()
                        x['bill'] = bill.id
                        data.append(x)
                    else:
                        data.append(x)

                # bulk create the operations serializer
                serializer = PreOperationSerializer(data=data, many=True, context={'request': request})
                if serializer.is_valid():
                    serializer.save()
                    return response({'error': False, 'data': serializer.data}, 200)
                else:
                    return response({'error': True, 'data': serializer.errors}, 200)

        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)