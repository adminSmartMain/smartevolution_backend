# REST Framework imports
from rest_framework.decorators import APIView
from django.db.models import Q, Count
from rest_framework import serializers
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

from django.db import transaction
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import uuid
from apps.base.utils.index import gen_uuid, PDFBase64File, uploadFileBase64

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
def is_uuid(val):
        try:
            uuid.UUID(str(val))
            return True
        except ValueError:
            return False

# REST Framework imports
from rest_framework.decorators import APIView
from django.db.models import Q, Count
from rest_framework import serializers
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

from django.db import transaction
from rest_framework.response import Response
from rest_framework import status

import uuid


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
def is_uuid(val):
        try:
            uuid.UUID(str(val))
            return True
        except ValueError:
            return False

class PreOperationAV(BaseAV):
    @transaction.atomic
    @checkRole(['admin'])
    def post(self, request):
        try:
            # ==================== INITIAL SETUP ====================
            logger.info(f"PreOperationAV request received from {request.user}")
            
            # Parse and validate request data
            try:
                json_data = json.loads(request.body.decode('utf-8'))
                values_list = json_data.get('values', [])
                if not values_list:
                    return response(
                        {'error': True, 'message': 'Empty values list provided'},
                        status.HTTP_400_BAD_REQUEST
                    )
            except json.JSONDecodeError:
                return response(
                    {'error': True, 'message': 'Invalid JSON data'},
                    status.HTTP_400_BAD_REQUEST
                )

            logger.debug(f"Processing {len(values_list)} operation(s)")

            # ==================== SINGLE OPERATION ====================
            if len(values_list) == 1:
                return self._handle_single_operation(request, values_list[0])

            # ==================== BULK OPERATIONS ====================
            return self._handle_bulk_operations(request, values_list)

        except Exception as e:
            logger.exception("Unexpected error in PreOperationAV")
            return response(
                {'error': True, 'message': 'Internal server error'},
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _handle_single_operation(self, request, operation_data):
        """Process single operation with atomic creation of bill if needed"""
        try:
            with transaction.atomic():
                # Create bill if billCode exists
                bill_id = None
                if operation_data.get('billCode', '') != '':
                    bill_id = self._create_or_get_bill(operation_data)
                    operation_data['bill'] = bill_id

                # Validate and save operation
                serializer = PreOperationSerializer(
                    data=operation_data,
                    context={'request': request}
                )
                
                if not serializer.is_valid():
                    logger.error(f"Validation failed: {serializer.errors}")
                    raise serializers.ValidationError(serializer.errors)

                instance = serializer.save()
                
                logger.info(f"Created operation {instance.id} with bill {bill_id or 'none'}")
                
                return response({
                    'error': False,
                    'message': 'Operation created successfully',
                    'data': serializer.data,
                    'with_bill': bool(bill_id)
                }, status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Failed to create operation: {str(e)}")
            return response(
                {'error': True, 'message': str(e)},
                getattr(e, 'status_code', status.HTTP_400_BAD_REQUEST)
            )

    def _handle_bulk_operations(self, request, values_list):
        operations_created = []
        errors = []
        bill_mapping = {}

        try:
            with transaction.atomic():
                # Fase 1: Mapeo de todas las facturas referenciadas
                all_bill_refs = set()
                
                # Identificar todas las referencias a facturas (tanto por billCode como por bill)
                for op_data in values_list:
                    if op_data.get('billCode', ''):
                        all_bill_refs.add(op_data['billCode'])
                    elif op_data.get('bill', ''):
                        # Si es un UUID válido, no necesitamos mapearlo
                        if not is_uuid(op_data['bill']):
                            all_bill_refs.add(op_data['bill'])
                
                # Obtener facturas existentes
                existing_bills = Bill.objects.filter(billId__in=all_bill_refs)
                bill_mapping = {bill.billId: str(bill.id) for bill in existing_bills}
                logger.debug(f"Facturas existentes mapeadas: {bill_mapping}")

                # Crear facturas nuevas (solo primera ocurrencia)
                for index, op_data in enumerate(values_list):
                    bill_code = op_data.get('billCode', '')
                    if bill_code and bill_code not in bill_mapping and op_data.get('_isFirstOccurrence', False):
                        try:
                            bill_id = self._create_or_get_bill(op_data)
                            bill_mapping[bill_code] = bill_id
                            logger.info(f"Factura creada: {bill_code} -> {bill_id}")
                        except Exception as e:
                            logger.error(f"Error creando factura {bill_code}: {str(e)}")
                            errors.append({
                                'index': index,
                                'error': f"Error creando factura {bill_code}: {str(e)}",
                                'data': op_data
                            })

                if errors:
                    raise Exception("Error en creación de facturas")

                # Fase 2: Procesar operaciones
                for index, op_data in enumerate(values_list):
                    if any(err['index'] == index for err in errors):
                        continue

                    try:
                        operation_data = {**op_data}
                        bill_ref = None
                        
                        # Caso 1: Tiene billCode (nueva factura)
                        if op_data.get('billCode', ''):
                            bill_ref = op_data['billCode']
                            if bill_ref in bill_mapping:
                                operation_data['bill'] = bill_mapping[bill_ref]
                            else:
                                raise ValueError(f"Factura {bill_ref} no existe")
                        
                        # Caso 2: Tiene bill que no es UUID (referencia por billId)
                        elif op_data.get('bill', '') and not is_uuid(op_data['bill']):
                            bill_ref = op_data['bill']
                            if bill_ref in bill_mapping:
                                operation_data['bill'] = bill_mapping[bill_ref]
                            else:
                                raise ValueError(f"Factura {bill_ref} no existe")
                        
                        # Caso 3: Tiene bill que es UUID (ya está correcto)
                        
                        serializer = PreOperationSerializer(
                            data=operation_data,
                            context={'request': request}
                        )
                        
                        if not serializer.is_valid():
                            logger.error(f"Error validación operación {index}: {serializer.errors}")
                            raise serializers.ValidationError(serializer.errors)
                        
                        instance = serializer.save()
                        operations_created.append({
                            'index': index,
                            'operation_id': str(instance.id),
                            'bill_id': operation_data.get('bill')
                        })

                    except Exception as e:
                        logger.error(f"Error en operación {index}: {str(e)}")
                        errors.append({
                            'index': index,
                            'error': str(e),
                            'data': op_data
                        })

                if errors:
                    raise Exception("Algunas operaciones fallaron")

                return response({
                    'total_operations': len(values_list),
                    'successful': operations_created,
                    'failed': errors,
                    'bill_mapping': bill_mapping
                }, status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error en operación masiva: {str(e)}")
            return response({
                'error': True,
                'message': 'Operaciones fallidas',
                'details': errors,
                'successful_count': len(operations_created)
            }, status.HTTP_400_BAD_REQUEST)

    def _create_or_get_bill(self, operation_data):
        """Helper to create or get existing bill"""
        bill_code = operation_data['billCode']
        logger.debug(operation_data)
        try:
            # Try to get existing bill first
            logger.debug("aaaaaa donde creao")
            bill = Bill.objects.filter(billId=bill_code).first()
            logger.debug("paso aaa")
            if bill:
                return str(bill.id)
            logger.debug("1")
            # Create new bill
            emitter = Client.objects.get(pk=operation_data['emitter'])
            payer = Client.objects.get(pk=operation_data['payer'])
            type_bill = TypeBill.objects.get(pk='fdb5feb4-24e9-41fc-9689-31aff60b76c9')
            logger.debug("2")

            if 'file' in operation_data:
                fileUrl = operation_data.get('file', None)
                if fileUrl:
                    fileUrl = uploadFileBase64(files_bse64=[fileUrl], file_path=f'bill/{operation_data["id"]}')
                    operation_data['file'] = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{fileUrl}"
                    
            bill = Bill.objects.create(
                id=gen_uuid(),
                typeBill=type_bill,
                billId=bill_code,
                emitterId=emitter.document_number,
                emitterName=emitter.social_reason or f"{emitter.first_name} {emitter.last_name}",
                payerId=payer.document_number,
                payerName=payer.social_reason or f"{payer.first_name} {payer.last_name}",
                billValue=operation_data['saldoInicialFactura'],
                subTotal=operation_data['saldoInicialFactura'],
                total=operation_data['saldoInicialFactura'],
                currentBalance=operation_data.get('currentBalance', operation_data['saldoInicialFactura']),
                dateBill=operation_data['DateBill'],
                datePayment=operation_data['DateExpiration'],
                expirationDate=operation_data['DateExpiration'],
                file=operation_data['file']
                
            )
            
            return str(bill.id)
        except Exception as e:
            logger.error(f"Bill creation failed for {bill_code}: {str(e)}")
            raise

    def _prepare_operation_data(self, op_data, client_map, bill_mapping):
        """Prepare clean operation data with validation"""
        operation_data = {}
        
        # Validate required fields
        required_fields = ['emitter', 'payer', 'DateBill', 'DateExpiration']
        for field in required_fields:
            if field not in op_data:
                raise ValueError(f"Missing required field: {field}")
            operation_data[field] = op_data[field]

        # Handle bill reference
        if op_data.get('billCode', '') != '':
            bill_code = op_data['billCode']
            if bill_code in bill_mapping:
                operation_data['bill'] = bill_mapping[bill_code]
            else:
                raise ValueError(f"Bill {bill_code} does not exist in mapping")

        # Copy other fields
        for k, v in op_data.items():
            if k not in ['billCode', '_isFirstOccurrence'] and k not in required_fields:
                operation_data[k] = v

        return operation_data
    
    @checkRole(['admin'])
    def get(self, request, pk=None):
        
        try:

            if pk:
                logger.debug(f"PreOperationAV pk")
                if len(request.query_params) > 0:
                    preOperation  = PreOperation.objects.get(pk=request.query_params.get('id'))
                    serializer    = PreOperationReadOnlySerializer(preOperation)
                    return response({'error': False, 'data': serializer.data}, 200)
                else:
                    logger.debug(f"PreOperationAV pk else")
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
                logger.debug(f"PreOperationAV if 2")
                if (request.query_params.get('opId') != 'undefined') and (request.query_params.get('notifications') == 'electronicSignature'):
                    
                    # get the operation data
                    
                    preOperation = PreOperation.objects.filter(opId=request.query_params.get('opId'))
                    serializer   = PreOperationReadOnlySerializer(preOperation, many=True)
                    logger.debug(f"  data de buscar por opID{ serializer.data}")
                    for obj in preOperation:
                       logger.debug(f"  preOperation filtro  de buscar por opID{vars(obj)}")
                   
                    
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
                            logger.debug(f" if uno")
                            filteredOperations.append(x)
                        else:
                            logger.debug(f" else uno")
                            for y in filteredOperations:
                                logger.debug(f" entro al for")
                                if x.investor == y.investor and x.opId == y.opId:
                                    y.payedAmount += x.payedAmount
                                    y.presentValueInvestor += x.presentValueInvestor
                                    logger.debug(f" y.investorTax {y.investorTax}")
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
                                
                                
                            logger.debug(f" y.investorTax {y.investorTax}")         
                    
                   
                    if x.investorTax:
                        y.investorTax=round(y.investorTax/n,2)
                    
                    page = self.paginate_queryset(filteredOperations)
                    if page is not None:
                        serializer   = PreOperationSignatureSerializer(page, many=True)
                        return self.get_paginated_response(serializer.data)
                   
                elif  request.query_params.get('investor') and request.query_params.get('status'):
                    logger.debug(f"investor y status están definidos")
                    
                    # Obtener los datos de la operación
                    preOperation = PreOperation.objects.filter(
                        investor_id=request.query_params.get('investor'),
                        status=request.query_params.get('status')
                    )
                    serializer = PreOperationReadOnlySerializer(preOperation, many=True)
                    
                    return response({'error': False, 'data': serializer.data}, 200)
                
                elif (request.query_params.get('opId') != 'undefined'):
                    logger.debug(f"request.query_params.get('opId') != 'undefined'")
                    data = generateSellOffer(request.query_params.get('opId'))
                    # get the operation data
                    
                    preOperation = PreOperation.objects.filter(opId=request.query_params.get('opId'))
                    serializer   = PreOperationReadOnlySerializer(preOperation, many=True)
                    
                    data['investor']['investorAccount'] = serializer.data[0]['clientAccount']
                    return response({'error': False, 'data': data}, 200)
                elif request.query_params.get('opIdV') != 'undefined':
                    logger.debug(f"request.query_params.get('opIdV') != 'undefined'")
                    #ACA SE TOMAN LOS DATOS AL MOMENTO DE PRESIONAR AL WHATSAPP
                    data = calcOperationDetail(request.query_params.get('opIdV'), request.query_params.get('investor')) 
                    return response({'error': False, 'data': data}, 200)
                elif request.query_params.get('notifications') == 'electronicSignature' and request.query_params.get('nOpId') == 'undefined':
                    logger.debug(f"request.query_params.get('notifications') == 'electronicSignature' and request.query_params.get('nOpId') == 'undefined'")
                    if 'investor' in request.query_params:
                        logger.debug(f"  investir  de buscar por investor")
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
                logger.debug(f"else final")
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
                logger.debug('a')
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
                logger.debug('bbbbbbbbbbbbbb')
                preOperation = PreOperation.objects.get(pk=pk)
                serializer   = PreOperationSerializer(preOperation, data=request.data, context={'request': request}, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return response({'error': False, 'data': serializer.data}, 200)
                else:
                    return response({'error': True, 'message': serializer.errors}, 500)
            elif request.data['massive'] == True:

                logger.debug('c')
                preOperation = PreOperation.objects.get(pk=pk)
                if request.data['status'] == 2:
                    # get the operations with the same opId
                    operations = PreOperation.objects.filter(opId=preOperation.opId, investor=preOperation.investor)
                    for operation in operations:
                        operation.status = 2
                        

                        log_balance_change(operation.clientAccount, operation.clientAccount.balance, (operation.clientAccount.balance + operation.presentValueInvestor), operation.presentValueInvestor, 'pre_operation', operation.id, 'PreOperation View - patch')
                        operation.clientAccount.balance += operation.presentValueInvestor
                        log_balance_change(operation.clientAccount, operation.clientAccount.balance, (operation.clientAccount.balance + operation.GM), operation.GM, 'pre_operation', operation.id, 'PreOperation View - patch 2')
                        operation.clientAccount.balance += operation.GM
                        operation.bill.save()
                        operation.clientAccount.save()
                        operation.save()
                    return response({'error': False, 'message': 'Operaciones Actualizada'}, 200)
                else:
                    logger.debug('d')
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
                logger.debug('e')
                preOperation = PreOperation.objects.filter(opId=request.data['opId'], investor=request.data['investor'])
                for operations in preOperation:
                    if request.data['status'] == 2:
                        operations.status = 2
                       
                        
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
                    logger.debug('f')
                    # get the operations with the same opId
                    operations = PreOperation.objects.filter(opId=preOperation.opId)
                    for operation in operations:
                        operation.status = 1
                        operation.save()    



                return response({'error': False, 'message': 'Operaciones Actualizada'}, 200)

            else:
                logger.debug('ag')
                preOperation = PreOperation.objects.get(pk=pk)


                logger.debug('caso editar',preOperation,request.data)
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
            preOperation.bill.currentBalance   += preOperation.amount
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
            elif (request.query_params.get('opId') != '' and request.query_params.get('investor') != '' and request.query_params.get('billId') == '' and request.query_params.get('mode') =='operations'):
                logger.debug(f"caso opID e investor operations")
                preOperations = PreOperation.objects.filter(opId=request.query_params.get('opId')).filter(Q(investor__last_name__icontains=request.query_params.get('investor')) |
                                                            Q(investor__first_name__icontains=request.query_params.get('investor')) |
                                                            Q(investor__social_reason__icontains=request.query_params.get('investor')) |
                                                            Q(emitter__last_name__icontains=request.query_params.get('investor')) |
                                                            Q(emitter__first_name__icontains=request.query_params.get('investor')) |
                                                            Q(emitter__social_reason__icontains=request.query_params.get('investor'))
            )
            elif (request.query_params.get('opId') != '' and request.query_params.get('investor') != '' and request.query_params.get('billId') == ''):
                logger.debug(f"caso opID e investor preoperations")
                preOperations = PreOperation.objects.filter(
                opId=request.query_params.get('opId'),
                status__lte=3).filter(
                Q(investor__last_name__icontains=request.query_params.get('investor')) |
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
            elif (request.query_params.get('opId') == '' and request.query_params.get('billId') == '' and request.query_params.get('investor') == '' and request.query_params.get('mode') =='operations'):
                logger.debug(f"modo operations sin mas parametros")
                preOperations = PreOperation.objects.all()

            elif (request.query_params.get('opId') != '' and request.query_params.get('billId') == '' and request.query_params.get('investor') == '' and request.query_params.get('startDate') == '' and request.query_params.get('endDate') == '' and request.query_params.get('mode') =='operations'):
                logger.debug(f"a modo operations" )
                preOperations = PreOperation.objects.filter(opId=request.query_params.get('opId'), status__lte=4)


            elif (request.query_params.get('opId') == '' and request.query_params.get('billId') != '' and request.query_params.get('investor') == '' and request.query_params.get('startDate') == '' and request.query_params.get('endDate') == '' and request.query_params.get('mode') =='operations'):                
                logger.debug(f"b modo operations")
                preOperations = PreOperation.objects.filter(bill_id__billId__icontains=request.query_params.get('billId'))

            elif (request.query_params.get('opId') == '' and request.query_params.get('billId') == '' and request.query_params.get('investor') != '' and request.query_params.get('startDate') == '' and request.query_params.get('endDate') == '' and request.query_params.get('mode') =='operations'):
                logger.debug(f"c modo operations")
                preOperations = PreOperation.objects.filter(Q(investor__last_name__icontains=request.query_params.get('investor')) |
                                                            Q(investor__first_name__icontains=request.query_params.get('investor')) |
                                                            Q(investor__social_reason__icontains=request.query_params.get('investor')) |
                                                            Q(emitter__last_name__icontains=request.query_params.get('investor')) |
                                                            Q(emitter__first_name__icontains=request.query_params.get('investor')) |
                                                          Q(emitter__social_reason__icontains=request.query_params.get('investor')))
            
            elif (request.query_params.get('opId') == '' and request.query_params.get('billId') == '' and request.query_params.get('investor') == '' and request.query_params.get('startDate') != '' and request.query_params.get('endDate') != '' and request.query_params.get('mode') =='operations'):
                logger.debug(f"a con fecha sin mas parametros modo operations")
                preOperations = PreOperation.objects.filter(
                    opDate__gte=request.query_params.get('startDate'),
                    opDate__lte=request.query_params.get('endDate')
                )
            elif (request.query_params.get('opId') != '' and request.query_params.get('billId') == '' and request.query_params.get('investor') == '' and request.query_params.get('startDate') != '' and request.query_params.get('endDate') != '' and request.query_params.get('mode') =='operations'):
                logger.debug(f"a con fecha modo operations")
                preOperations = PreOperation.objects.filter(
                    opId=request.query_params.get('opId'),
                    status__lte=4,
                    opDate__gte=request.query_params.get('startDate'),
                    opDate__lte=request.query_params.get('endDate')
                )

            elif (request.query_params.get('opId') == '' and request.query_params.get('billId') != '' and request.query_params.get('investor') == '' and request.query_params.get('startDate') != '' and request.query_params.get('endDate') != '' and request.query_params.get('mode') =='operations'):                
                logger.debug(f"b con fecha modo operations")
                preOperations = PreOperation.objects.filter(
                    bill_id__billId__icontains=request.query_params.get('billId'),
                    opDate__gte=request.query_params.get('startDate'),
                    opDate__lte=request.query_params.get('endDate')
                )

            elif (request.query_params.get('opId') == '' and request.query_params.get('billId') == '' and request.query_params.get('investor') != '' and request.query_params.get('startDate') != '' and request.query_params.get('endDate') != '' and request.query_params.get('mode') =='operations'):
                logger.debug(f"c fecha modo operations")
                preOperations = PreOperation.objects.filter(
                    Q(investor__last_name__icontains=request.query_params.get('investor')) |
                    Q(investor__first_name__icontains=request.query_params.get('investor')) |
                    Q(investor__social_reason__icontains=request.query_params.get('investor')) |
                    Q(emitter__last_name__icontains=request.query_params.get('investor')) |
                    Q(emitter__first_name__icontains=request.query_params.get('investor')) |
                    Q(emitter__social_reason__icontains=request.query_params.get('investor')),
                    opDate__gte=request.query_params.get('startDate'),
                    opDate__lte=request.query_params.get('endDate')
                )
            elif (request.query_params.get('opId') != '' and request.query_params.get('billId') == '' and request.query_params.get('investor') == '' and request.query_params.get('mode') =='operations'):
                logger.debug(f"a c0n mode operations")
                preOperations = PreOperation.objects.filter(opId=request.query_params.get('opId'), status__lte=4)
            elif (request.query_params.get('opId') != '' and request.query_params.get('billId') == '' and request.query_params.get('investor') == '' and request.query_params.get('startDate') == '' and request.query_params.get('endDate') == ''):
                logger.debug(f"a")
                preOperations = PreOperation.objects.filter(opId=request.query_params.get('opId'), status__lte=4)


            elif (request.query_params.get('opId') == '' and request.query_params.get('billId') != '' and request.query_params.get('investor') == '' and request.query_params.get('startDate') == '' and request.query_params.get('endDate') == ''):                
                logger.debug(f"b")
                preOperations = PreOperation.objects.filter(bill_id__billId__icontains=request.query_params.get('billId'))

            elif (request.query_params.get('opId') == '' and request.query_params.get('billId') == '' and request.query_params.get('investor') != '' and request.query_params.get('startDate') == '' and request.query_params.get('endDate') == ''):
                logger.debug(f"c")
                preOperations = PreOperation.objects.filter(Q(investor__last_name__icontains=request.query_params.get('investor')) |
                                                            Q(investor__first_name__icontains=request.query_params.get('investor')) |
                                                            Q(investor__social_reason__icontains=request.query_params.get('investor')) |
                                                            Q(emitter__last_name__icontains=request.query_params.get('investor')) |
                                                            Q(emitter__first_name__icontains=request.query_params.get('investor')) |
                                                          Q(emitter__social_reason__icontains=request.query_params.get('investor')))
            
            elif (request.query_params.get('opId') == '' and request.query_params.get('billId') == '' and request.query_params.get('investor') == '' and request.query_params.get('startDate') != '' and request.query_params.get('endDate') != ''):
                logger.debug(f"a con fecha sin mas parametros")
                preOperations = PreOperation.objects.filter(
                    opDate__gte=request.query_params.get('startDate'),
                    opDate__lte=request.query_params.get('endDate')
                )
            elif (request.query_params.get('opId') != '' and request.query_params.get('billId') == '' and request.query_params.get('investor') == '' and request.query_params.get('startDate') != '' and request.query_params.get('endDate') != ''):
                logger.debug(f"a con fecha")
                preOperations = PreOperation.objects.filter(
                    opId=request.query_params.get('opId'),
                    status__lte=4,
                    opDate__gte=request.query_params.get('startDate'),
                    opDate__lte=request.query_params.get('endDate')
                )

            elif (request.query_params.get('opId') == '' and request.query_params.get('billId') != '' and request.query_params.get('investor') == '' and request.query_params.get('startDate') != '' and request.query_params.get('endDate') != ''):                
                logger.debug(f"b con fecha")
                preOperations = PreOperation.objects.filter(
                    bill_id__billId__icontains=request.query_params.get('billId'),
                    opDate__gte=request.query_params.get('startDate'),
                    opDate__lte=request.query_params.get('endDate')
                )

            elif (request.query_params.get('opId') == '' and request.query_params.get('billId') == '' and request.query_params.get('investor') != '' and request.query_params.get('startDate') != '' and request.query_params.get('endDate') != ''):
                logger.debug(f"c fecha")
                preOperations = PreOperation.objects.filter(
                    Q(investor__last_name__icontains=request.query_params.get('investor')) |
                    Q(investor__first_name__icontains=request.query_params.get('investor')) |
                    Q(investor__social_reason__icontains=request.query_params.get('investor')) |
                    Q(emitter__last_name__icontains=request.query_params.get('investor')) |
                    Q(emitter__first_name__icontains=request.query_params.get('investor')) |
                    Q(emitter__social_reason__icontains=request.query_params.get('investor')),
                    opDate__gte=request.query_params.get('startDate'),
                    opDate__lte=request.query_params.get('endDate')
                )
            else:
                logger.debug(f"d")
                preOperations = PreOperation.objects.all()

            if (request.query_params.get('mode') != '' and request.query_params.get('mode') != None):
                logger.debug(f"f")
                possibleStatus = [1, 3, 4, 5]
                preOperations = list(filter(lambda x: x.status in possibleStatus, preOperations))
                
            logger.debug(f"g")
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
                logger.debug(f"h")
                page = self.paginate_queryset(preOperations)
                if page is not None:
                    logger.debug(f"i")
                    serializer   = PreOperationByParamsSerializer(page, many=True)
                    return self.get_paginated_response(serializer.data)
            typeClient = preOperations[0].emitter.type_client.id
            try:
                logger.debug(f"j")
                riskProfile = RiskProfile.objects.get(client = preOperations[0].emitter.id)
            except RiskProfile.DoesNotExist:
                riskProfile = None
            # calc commission
            logger.debug(f"k")
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
                
                logger.debug(f"l")
                serializer   = PreOperationByParamsSerializer(page, many=True)
                logger.debug(f"m")
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