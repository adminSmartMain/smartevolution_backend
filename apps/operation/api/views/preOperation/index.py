# REST Framework imports
from rest_framework.decorators import APIView
from django.db.models import Q, Count
from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, Max
# Models
from apps.client.models import Client, RiskProfile, Account, Broker
from apps.operation.models import PreOperation, Receipt, BuyOrder,OperationLog
from apps.bill.models import Bill
from apps.misc.models import TypeBill
# Serializers
from apps.operation.api.serializers.index import (PreOperationSerializer, PreOperationReadOnlySerializer, 
                                                  ReceiptSerializer, PreOperationSignatureSerializer, PreOperationByParamsSerializer)
from apps.operation.utils.operation_logger import create_operation_log, create_exception_log
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
from collections import defaultdict
from django.db import transaction, connection
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import uuid
from apps.base.utils.index import gen_uuid, PDFBase64File, uploadFileBase64
from apps.base.utils.s3logging import log_execution_to_s3

from django.db.models import Max
from datetime import date
from django.db import transaction
from datetime import date
from django.db import transaction

from apps.operation.utils.upload_excel_parser import UploadExcelParser
from apps.operation.utils.upload_excel_resolver import UploadExcelReferenceResolver
from apps.operation.utils.upload_excel_calculator import UploadExcelCalculator
from apps.operation.utils.upload_excel_validator import UploadExcelValidator
from apps.operation.utils.upload_excel_response import UploadExcelResponseBuilder
from apps.bill.api.serializers.index import BillSerializer
import base64
import time
from decimal import Decimal

from django.http import HttpResponse
from django.template.loader import get_template
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework import status


from apps.operation.models import PreOperation
from apps.base.utils.pdfToBase64 import pdfToBase64



from apps.operation.api.models.index import MassiveOperationDraft, PreOperation
from apps.operation.api.serializers.index import MassiveOperationDraftSerializer, MassiveOperationDraftListSerializer, PreOperationReadOnlySerializer
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
from django.utils import timezone
from datetime import date


from rest_framework.views import APIView
from django.db.models import Count

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

            if len(values_list) == 1:
                return self._handle_single_operation(request, values_list[0])

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
                bill_id = None

                if operation_data.get('billCode', '') != '' and operation_data.get('_isFirstOccurrence', False):
                    bill_id = self._create_or_get_bill(operation_data, request=request)
                    operation_data['bill'] = bill_id

                elif operation_data.get('bill', '') and is_uuid(operation_data['bill']):
                    bill_id = operation_data['bill']

                elif operation_data.get('bill', '') and not is_uuid(operation_data['bill']):
                    emitter_id = operation_data.get('emitter')
                    if not emitter_id:
                        raise ValueError("Se requiere emitter para buscar la factura por billId")

                    try:
                        emitter_client = Client.objects.get(pk=emitter_id)
                        emitter_doc_number = emitter_client.document_number
                    except Client.DoesNotExist:
                        raise ValueError(f"Emisor con ID {emitter_id} no encontrado")

                    bill = Bill.objects.filter(
                        billId=operation_data['bill'],
                        emitterId=emitter_doc_number
                    ).first()

                    if bill:
                        operation_data['bill'] = str(bill.id)
                        bill_id = str(bill.id)
                    else:
                        raise ValueError(
                            f"Factura con billId {operation_data['bill']} y emisor {emitter_doc_number} no encontrada"
                        )

                serializer = PreOperationSerializer(
                    data=operation_data,
                    context={'request': request}
                )

                if not serializer.is_valid():
                    logger.error(f"Validation failed: {serializer.errors}")
                    raise serializers.ValidationError(serializer.errors)

                instance = serializer.save()

                log_operation_data = dict(operation_data)
                log_response_data = {
                    "id": str(instance.id),
                    "bill_id": str(bill_id) if bill_id else None,
                }

                transaction.on_commit(lambda instance=instance, log_operation_data=log_operation_data, log_response_data=log_response_data: create_operation_log(
                    source="SINGLE",
                    action="CREATE_SINGLE_OPERATION",
                    status="SUCCESS",
                    message="Operation created successfully",
                    op_id=instance.opId,
                    pre_operation=instance,
                    request_payload=log_operation_data,
                    response_payload=log_response_data,
                    bill_code=log_operation_data.get("billCode"),
                    bill_id_ref=log_operation_data.get("bill"),
                    user=request.user,
                ))

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

        try:
            with transaction.atomic():
                bills_to_create = {}
                existing_bills_to_find = {}

                for index, op_data in enumerate(values_list):
                    if op_data.get('billCode', '') and op_data.get('_isFirstOccurrence', False):
                        bill_code = op_data['billCode']
                        if bill_code not in bills_to_create:
                            bills_to_create[bill_code] = op_data

                    elif op_data.get('bill', '') and not is_uuid(op_data['bill']):
                        bill_id_ref = op_data['bill']
                        emitter_id = op_data.get('emitter')

                        if emitter_id:
                            key = f"{bill_id_ref}_{emitter_id}"
                            existing_bills_to_find[key] = {
                                'billId': bill_id_ref,
                                'emitterId': emitter_id,
                                'indexes': existing_bills_to_find.get(key, {}).get('indexes', []) + [index]
                            }
                        else:
                            errors.append({
                                'index': index,
                                'error': "Se requiere emitter para buscar factura existente",
                                'data': op_data
                            })

                bill_mapping = {}
                for bill_code, op_data in bills_to_create.items():
                    try:
                        bill_id = self._create_or_get_bill(op_data, request=request)
                        bill_mapping[bill_code] = bill_id
                        logger.info(f"Factura creada: {bill_code} -> {bill_id}")
                    except Exception as e:
                        logger.error(f"Error creando factura {bill_code}: {str(e)}")
                        for index, item in enumerate(values_list):
                            if item.get('billCode') == bill_code:
                                errors.append({
                                    'index': index,
                                    'error': f"Error creando factura {bill_code}: {str(e)}",
                                    'data': item
                                })

                if existing_bills_to_find:
                    emitter_ids = [item['emitterId'] for item in existing_bills_to_find.values()]
                    emitters = Client.objects.filter(id__in=emitter_ids)
                    emitter_map = {str(emitter.id): emitter.document_number for emitter in emitters}

                    for key, bill_info in existing_bills_to_find.items():
                        bill_id_ref = bill_info['billId']
                        emitter_client_id = bill_info['emitterId']
                        emitter_doc_number = emitter_map.get(emitter_client_id)

                        if not emitter_doc_number:
                            for index in bill_info['indexes']:
                                errors.append({
                                    'index': index,
                                    'error': f"Emisor con ID {emitter_client_id} no encontrado",
                                    'data': values_list[index]
                                })
                            continue

                        bill = Bill.objects.filter(
                            billId=bill_id_ref,
                            emitterId=emitter_doc_number
                        ).first()

                        if bill:
                            bill_mapping[key] = str(bill.id)
                        else:
                            for index in bill_info['indexes']:
                                errors.append({
                                    'index': index,
                                    'error': f"Factura con billId {bill_id_ref} y emisor {emitter_doc_number} no encontrada",
                                    'data': values_list[index]
                                })

                for index, op_data in enumerate(values_list):
                    if any(err['index'] == index for err in errors):
                        continue

                    try:
                        operation_data = {**op_data}

                        if op_data.get('billCode', ''):
                            bill_code = op_data['billCode']
                            if bill_code in bill_mapping:
                                operation_data['bill'] = bill_mapping[bill_code]
                            else:
                                raise ValueError(f"Factura {bill_code} no encontrada en el mapeo")

                        elif op_data.get('bill', '') and not is_uuid(op_data['bill']):
                            bill_id_ref = op_data['bill']
                            emitter_id = op_data.get('emitter')

                            if not emitter_id:
                                raise ValueError("Se requiere emitter para buscar factura existente")

                            key = f"{bill_id_ref}_{emitter_id}"

                            if key in bill_mapping:
                                operation_data['bill'] = bill_mapping[key]
                            else:
                                try:
                                    emitter_client = Client.objects.get(pk=emitter_id)
                                    emitter_doc_number = emitter_client.document_number

                                    bill = Bill.objects.filter(
                                        billId=bill_id_ref,
                                        emitterId=emitter_doc_number
                                    ).first()

                                    if bill:
                                        operation_data['bill'] = str(bill.id)
                                        bill_mapping[key] = str(bill.id)
                                    else:
                                        raise ValueError(
                                            f"Factura con billId {bill_id_ref} y emisor {emitter_doc_number} no encontrada"
                                        )
                                except Client.DoesNotExist:
                                    raise ValueError(f"Emisor con ID {emitter_id} no encontrado")

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

                        transaction.on_commit(
                            lambda instance=instance, index=index, operation_data=operation_data: create_operation_log(
                                source="BULK",
                                action="CREATE_BULK_ROW",
                                status="SUCCESS",
                                message=f"Fila {index} creada correctamente",
                                op_id=instance.opId,
                                pre_operation=instance,
                                row_index=index,
                                request_payload=operation_data,
                                response_payload={
                                    "operation_id": str(instance.id),
                                    "bill_id": operation_data.get("bill")
                                },
                                bill_code=operation_data.get("billCode"),
                                bill_id_ref=operation_data.get("bill"),
                                user=request.user,
                            )
                        )

                    except Exception as e:
                        logger.error(f"Error en operación {index}: {str(e)}")
                        errors.append({
                            'index': index,
                            'error': str(e),
                            'data': op_data
                        })

                if errors:
                    raise Exception("Algunas operaciones fallaron")

                transaction.on_commit(lambda: create_operation_log(
                    source="BULK",
                    action="BULK_SUMMARY",
                    status="SUCCESS",
                    message="Todas las operaciones fueron creadas correctamente",
                    op_id=values_list[0].get("opId") if values_list else None,
                    response_payload={
                        "successful_count": len(operations_created),
                        "failed_count": 0
                    },
                    user=request.user,
                ))

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

    def _create_or_get_bill(self, operation_data, request=None):
        """Helper to create or get existing bill by billId and emitterId"""
        bill_code = operation_data['billCode']

        try:
            emitter = Client.objects.get(pk=operation_data['emitter'])
            emitter_doc_number = emitter.document_number

            bill = Bill.objects.filter(
                billId=bill_code,
                emitterId=emitter_doc_number
            ).first()

            if bill:
                log_operation_data = dict(operation_data)
                log_response_data = {"bill_id": str(bill.id)}

                transaction.on_commit(lambda log_operation_data=log_operation_data, log_response_data=log_response_data: create_operation_log(
                    source="BILL",
                    action="FIND_OR_CREATE_BILL",
                    status="SUCCESS",
                    message="Factura creada correctamente",
                    op_id=log_operation_data.get("opId"),
                    request_payload=log_operation_data,
                    response_payload=log_response_data,
                    bill_code=bill_code,
                    user=request.user if request else None,
                ))
                return str(bill.id)

            payer = Client.objects.get(pk=operation_data['payer'])
            type_bill = TypeBill.objects.get(pk='fdb5feb4-24e9-41fc-9689-31aff60b76c9')

            file_url = None
            if 'file' in operation_data and operation_data['file']:
                file_url = uploadFileBase64(
                    files_bse64=[operation_data['file']],
                    file_path=f'bill/{operation_data.get("id", gen_uuid())}'
                )
                file_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{file_url}"

            bill = Bill.objects.create(
                id=gen_uuid(),
                typeBill=type_bill,
                billId=bill_code,
                emitterId=emitter_doc_number,
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
                file=file_url
            )

            transaction.on_commit(lambda: create_operation_log(
                source="BILL",
                action="FIND_OR_CREATE_BILL",
                status="SUCCESS",
                message="Factura creada correctamente",
                op_id=operation_data.get("opId"),
                request_payload=operation_data,
                response_payload={"bill_id": str(bill.id)},
                bill_code=bill_code,
                user=request.user if request else None,
            ))

            return str(bill.id)

        except Exception as e:
            logger.error(f"Bill creation failed for {bill_code}: {str(e)}")
            raise

    
    @checkRole(['admin'])
    def get(self, request, pk=None):
        
        try:

            if pk:
              
                if len(request.query_params) > 0:
                    preOperation  = PreOperation.objects.get(pk=request.query_params.get('id'))
                    serializer    = PreOperationReadOnlySerializer(preOperation)
                    return response({'error': False, 'data': serializer.data}, 200)
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
                                        
                                        n=n+1
                                    else:
                                        
                                        y.investorTax =(x.investorTax+y.investorTax)
                                   
                                    
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
                   
                elif  request.query_params.get('investor') and request.query_params.get('status'):
                    
                    # Obtener los datos de la operación
                    preOperation = PreOperation.objects.filter(
                        investor_id=request.query_params.get('investor'),
                        status=request.query_params.get('status')
                    )
                    serializer = PreOperationReadOnlySerializer(preOperation, many=True)
                    
                    return response({'error': False, 'data': serializer.data}, 200)
                
                elif (request.query_params.get('opId') != 'undefined'):
                   
                    data = generateSellOffer(request.query_params.get('opId'))
                    # get the operation data
                    
                    preOperation = PreOperation.objects.filter(opId=request.query_params.get('opId'))
                    serializer   = PreOperationReadOnlySerializer(preOperation, many=True)
                    
                    data['investor']['investorAccount'] = serializer.data[0]['clientAccount']
                    return response({'error': False, 'data': data}, 200)
                elif request.query_params.get('opIdV') != 'undefined':

                    #ACA SE TOMAN LOS DATOS AL MOMENTO DE PRESIONAR AL WHATSAPP
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

from django.db.models import Max

class GetBillFractionBulkAV(APIView):
    def post(self, request):
        try:
            bills = request.data.get("bills")

            if not bills or not isinstance(bills, list):
                return response(
                    {'error': True, 'message': "Debe enviar una lista en 'bills'"},
                    400
                )

            flat_rows = []

            for item in bills:
                pk = item.get("id") or item.get("billId")
                fractions_to_split = int(item.get("fractionsToSplit", 1) or 1)

                if not pk:
                    continue

                try:
                    bill = Bill.objects.get(pk=pk)

                    max_fraction = PreOperation.objects.filter(bill=pk).aggregate(
                        max_fraction=Max("billFraction")
                    )["max_fraction"]

                    start_fraction = (max_fraction or 0) + 1

                    bill_value = bill.currentBalance
                    date_bill = bill.dateBill
                    date_payment = bill.datePayment
                    expiration_date = bill.expirationDate

                except Bill.DoesNotExist:
                    continue
                except Exception:
                    continue

                for i in range(fractions_to_split):
                    flat_rows.append({
                        "id": f"{pk}-{start_fraction + i}",
                        "billUniqueId": str(pk),
                        "billId": item.get("billId", ""),
                        "currentBalance": bill_value,
                        "fraction": start_fraction + i,
                        "dateBill": date_bill,
                        "datePayment": date_payment,
                        "expirationDate": expiration_date,
                        "investorId": "",
                        "investorLabel": "",
                        "selectedInvestor": None,
                        "investorBrokerId": "",
                        "investorBrokerName": "",
                        "accountId": "",
                        "selectedAccount": None,
                        "availableAccounts": [],
                        "accountAvailableBalance": 0,
                        "accountTotalBalance": 0,
                    })

            return response({
                "error": False,
                "data": flat_rows
            }, 200)

        except Exception as e:
            return response(
                {'error': True, 'message': str(e)},
                e.status_code if hasattr(e, 'status_code') else 500
            )
            
            


class ClientsWithAccountsAV(APIView):
    def post(self, request):
        try:
            client_ids = request.data.get("client_ids", [])

            if not isinstance(client_ids, list) or not client_ids:
                return response(
                    {"error": True, "message": "Debe enviar una lista en 'client_ids'"},
                    400
                )

            clients = Client.objects.filter(id__in=client_ids)

            accounts_count_by_client = (
                Account.objects
                .filter(client_id__in=client_ids)
                .values("client_id")
                .annotate(accounts_count=Count("id"))
            )

            accounts_map = {
                str(item["client_id"]): item["accounts_count"]
                for item in accounts_count_by_client
            }

            data = []
            for client in clients:
                client_id = str(client.id)
                count = accounts_map.get(client_id, 0)

                data.append({
                    "client_id": client_id,
                    "has_accounts": count > 0,
                    "accounts_count": count,
                })

            return response({
                "error": False,
                "data": data,
            }, 200)

        except Exception as e:
            return response(
                {"error": True, "message": str(e)},
                e.status_code if hasattr(e, "status_code") else 500
            )
class GetOperationByEmitter(APIView):
    def get(self, request, pk):
        
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
        
        try:
            if (request.query_params.get('opId') != '' and request.query_params.get('billId') != '' and request.query_params.get('investor') != ''):
                preOperations = PreOperation.objects.filter(opId=request.query_params.get('opId'),  
                                                            bill_id__billId__icontains=request.query_params.get('investor'),status__in=[0, 2]
                                                            ).filter(Q(investor__last_name__icontains=request.query_params.get('investor')) |
                                                            Q(investor__first_name__icontains=request.query_params.get('investor')) |
                                                            Q(investor__social_reason__icontains=request.query_params.get('investor')) |
                                                   
                                                            Q(emitter__last_name__icontains=request.query_params.get('investor')) |
                                                            Q(emitter__first_name__icontains=request.query_params.get('investor')) |
                                                            Q(emitter__social_reason__icontains=request.query_params.get('investor')))

            elif (request.query_params.get('opId') != '' and request.query_params.get('billId') != '' and request.query_params.get('investor') == ''):
                preOperations = PreOperation.objects.filter(opId=request.query_params.get('opId'),
                                                            bill_id__billId__icontains=request.query_params.get('billId'),
                                                            status__in=[0, 2])
            elif (request.query_params.get('opId') != '' and request.query_params.get('investor') != '' and request.query_params.get('billId') == '' and request.query_params.get('mode') =='operations'):
                
                preOperations = PreOperation.objects.filter(opId=request.query_params.get('opId'),
                                                            status__in=[1, 3, 4, 5] 
                                                            ).filter(Q(investor__last_name__icontains=request.query_params.get('investor')) |
                                                            Q(investor__first_name__icontains=request.query_params.get('investor')) |
                                                            Q(investor__social_reason__icontains=request.query_params.get('investor')) |
                                                            Q(emitter__last_name__icontains=request.query_params.get('investor')) |
                                                            Q(emitter__first_name__icontains=request.query_params.get('investor')) |
                                                            Q(emitter__social_reason__icontains=request.query_params.get('investor'))
            )
            elif (request.query_params.get('opId') != '' and request.query_params.get('investor') != '' and request.query_params.get('billId') == ''):
           
                preOperations = PreOperation.objects.filter(
                opId=request.query_params.get('opId'),
                 status__in=[0, 2]).filter(
                Q(investor__last_name__icontains=request.query_params.get('investor')) |
                Q(investor__first_name__icontains=request.query_params.get('investor')) |
                Q(investor__social_reason__icontains=request.query_params.get('investor')) |
                Q(emitter__last_name__icontains=request.query_params.get('investor')) |
                Q(emitter__first_name__icontains=request.query_params.get('investor')) |
                Q(emitter__social_reason__icontains=request.query_params.get('investor'))
            )

            elif (request.query_params.get('billId') != '' and request.query_params.get('investor') != '' and request.query_params.get('opId') == ''):
               
                preOperations = PreOperation.objects.filter(bill_id__billId__icontains=request.query_params.get('billId'),
                                                             status__in=[0, 2]).filter(Q(investor__last_name__icontains=request.query_params.get('investor')) |
                                                            Q(investor__first_name__icontains=request.query_params.get('investor')) |
                                                            Q(investor__social_reason__icontains=request.query_params.get('investor')) |
                                                            Q(emitter__last_name__icontains=request.query_params.get('investor')) |
                                                            Q(emitter__first_name__icontains=request.query_params.get('investor')) |
                                                            Q(emitter__social_reason__icontains=request.query_params.get('investor'))
                                                             
)          
            elif (request.query_params.get('opId') == '' and request.query_params.get('billId') == '' and request.query_params.get('investor') == '' and request.query_params.get('mode') =='operations'and request.query_params.get('startDate') == '' and request.query_params.get('endDate') == '' and request.query_params.get('status') == ''):
            
                preOperations = PreOperation.objects.filter(status__in=[1, 3, 4, 5])

            elif (request.query_params.get('opId') != '' and request.query_params.get('billId') == '' and request.query_params.get('investor') == '' and request.query_params.get('startDate') == '' and request.query_params.get('endDate') == '' and request.query_params.get('mode') =='operations' and request.query_params.get('status') == ''):
               
                preOperations = PreOperation.objects.filter(opId=request.query_params.get('opId'), status__in=[1, 3, 4, 5])


            elif (request.query_params.get('opId') == '' and request.query_params.get('billId') != '' and request.query_params.get('investor') == '' and request.query_params.get('startDate') == '' and request.query_params.get('endDate') == '' and request.query_params.get('mode') =='operations' and request.query_params.get('status') == ''):                
             
                preOperations = PreOperation.objects.filter(bill_id__billId__icontains=request.query_params.get('billId'), status__in=[1, 3, 4, 5])

            elif (request.query_params.get('opId') == '' and request.query_params.get('billId') == '' and request.query_params.get('investor') != '' and request.query_params.get('startDate') == '' and request.query_params.get('endDate') == '' and request.query_params.get('mode') =='operations' and request.query_params.get('status') == ''):
                
                preOperations = PreOperation.objects.filter(status__in=[1, 3, 4, 5]).filter(Q(investor__last_name__icontains=request.query_params.get('investor')) |
                                                            Q(investor__first_name__icontains=request.query_params.get('investor')) |
                                                            Q(bill_id__billId__icontains=request.query_params.get('investor')) |
                                                            Q(investor__social_reason__icontains=request.query_params.get('investor')) |
                                                            Q(emitter__last_name__icontains=request.query_params.get('investor')) |
                                                            Q(emitter__first_name__icontains=request.query_params.get('investor')) |
                                                          Q(emitter__social_reason__icontains=request.query_params.get('investor'))
                                                          )
            
            elif (request.query_params.get('opId') == '' and request.query_params.get('billId') == '' and request.query_params.get('investor') == '' and request.query_params.get('startDate') != '' and request.query_params.get('endDate') != '' and request.query_params.get('mode') =='operations' and request.query_params.get('status') == ''):
                
                preOperations = PreOperation.objects.filter(
                    opDate__gte=request.query_params.get('startDate'),
                    opDate__lte=request.query_params.get('endDate'),
                    status__in=[1, 3, 4, 5]
                )
            elif (request.query_params.get('opId') != '' and request.query_params.get('billId') == '' and request.query_params.get('investor') == '' and request.query_params.get('startDate') != '' and request.query_params.get('endDate') != '' and request.query_params.get('mode') =='operations' and request.query_params.get('status') == ''):
                
                preOperations = PreOperation.objects.filter(
                    opId=request.query_params.get('opId'),
                    status__in=[1, 3, 4, 5],
                    opDate__gte=request.query_params.get('startDate'),
                    opDate__lte=request.query_params.get('endDate')
                )
            
            elif (request.query_params.get('opId') == '' and request.query_params.get('billId') != '' and request.query_params.get('investor') == '' and request.query_params.get('startDate') != '' and request.query_params.get('endDate') != '' and request.query_params.get('mode') =='operations' and request.query_params.get('status') == ''):                
                
                preOperations = PreOperation.objects.filter(
                     status__in=[1, 3, 4, 5],
                    bill_id__billId__icontains=request.query_params.get('billId'),
                    opDate__gte=request.query_params.get('startDate'),
                    opDate__lte=request.query_params.get('endDate')
                )

            elif (request.query_params.get('opId') == '' and request.query_params.get('billId') == '' and request.query_params.get('investor') != '' and request.query_params.get('startDate') != '' and request.query_params.get('endDate') != '' and request.query_params.get('mode') =='operations' and request.query_params.get('status') == ''):
                
                preOperations = PreOperation.objects.filter(
                    Q(investor__last_name__icontains=request.query_params.get('investor')) |
                    Q(investor__first_name__icontains=request.query_params.get('investor')) |
                    Q(investor__social_reason__icontains=request.query_params.get('investor')) |
                    Q(emitter__last_name__icontains=request.query_params.get('investor')) |
                    Q(emitter__first_name__icontains=request.query_params.get('investor')) |
                    Q(emitter__social_reason__icontains=request.query_params.get('investor')),
                    opDate__gte=request.query_params.get('startDate'),
                    opDate__lte=request.query_params.get('endDate'),
                     status__in=[1, 3, 4, 5],
                )
            elif (request.query_params.get('opId') != '' and request.query_params.get('billId') == '' and request.query_params.get('investor') == '' and request.query_params.get('mode') =='operations' and request.query_params.get('status') == ''):
                
                preOperations = PreOperation.objects.filter(opId=request.query_params.get('opId'),  status__in=[1, 3, 4, 5])
            
            elif (request.query_params.get('opId') == '' and request.query_params.get('billId') == '' and request.query_params.get('investor') == '' and request.query_params.get('startDate') == '' and request.query_params.get('endDate') == '' and request.query_params.get('status') != '' and request.query_params.get('mode') =='operations'):
                
                
                if request.query_params.get('status') == '5':
                    # Caso especial para status 5: operaciones expiradas (opExpiration < hoy) y status != 4
                    today = timezone.now().date()
                    preOperations = PreOperation.objects.filter(
                        opExpiration__lt=today
                    ).exclude(status=4)
                elif request.query_params.get('status') == '1':
                    today = timezone.now().date()
                    preOperations = PreOperation.objects.filter(opExpiration__gt=today, status=1)
                else:
                    preOperations = PreOperation.objects.filter(
                        
                    status__icontains=request.query_params.get('status')
                    )
                
            elif (request.query_params.get('opId') != '' and request.query_params.get('billId') == '' and request.query_params.get('investor') == '' and request.query_params.get('startDate') =='' and request.query_params.get('endDate') == '' and request.query_params.get('status') != '' and request.query_params.get('mode') =='operations'):
                
                
                if request.query_params.get('status') == '5':
                    # Caso especial para status 5: solo opExpiration < hoy y excluir status 4
                    today = timezone.now().date()
                    preOperations = PreOperation.objects.filter(
                        opId=request.query_params.get('opId'),
                        opExpiration__lt=today  # Solo esto, NO filtrar por status
                    ).exclude(status=4)  # Excluir operaciones con status 4
                    
                elif request.query_params.get('status') == '1':
                    today = timezone.now().date()
                    preOperations = PreOperation.objects.filter(opId=request.query_params.get('opId'),opExpiration__gt=today, status=1)
                else:
                    # Para otros status, usar la lógica normal
                    preOperations = PreOperation.objects.filter(
                        opId=request.query_params.get('opId'),  
                        status__icontains=request.query_params.get('status')
                    )
                
            elif (request.query_params.get('opId') == '' and request.query_params.get('billId') == '' and request.query_params.get('investor') == '' and request.query_params.get('startDate') != '' and request.query_params.get('endDate') != '' and request.query_params.get('status') != '' and request.query_params.get('mode') =='operations'):
               
                
                if request.query_params.get('status') == '5':
                    # Caso especial para status 5 con fechas
                    today = timezone.now().date()
                    preOperations = PreOperation.objects.filter(
                        opDate__gte=request.query_params.get('startDate'),
                        opDate__lte=request.query_params.get('endDate'),
                        opExpiration__lt=today
                    ).exclude(status=4)
                elif request.query_params.get('status') == '1':
                    today = timezone.now().date()
                    preOperations = PreOperation.objects.filter(
                        opDate__gte=request.query_params.get('startDate'),
                        opDate__lte=request.query_params.get('endDate'),
                        opExpiration__gt=today,
                        status=1
                    )
                else:
                    preOperations = PreOperation.objects.filter(
                        opDate__gte=request.query_params.get('startDate'),
                        opDate__lte=request.query_params.get('endDate'),
                        status__icontains=request.query_params.get('status')
                    )

            elif (request.query_params.get('opId') == '' and request.query_params.get('billId') == '' and request.query_params.get('investor')  !='' and request.query_params.get('startDate') != '' and request.query_params.get('endDate') != '' and request.query_params.get('status') != '' and request.query_params.get('mode') =='operations'):
                
                
                if request.query_params.get('status') == '5':
                    # Caso especial para status 5 con fechas e investor
                    today = timezone.now().date()
                    preOperations = PreOperation.objects.filter(
                        (Q(investor__last_name__icontains=request.query_params.get('investor')) |
                        Q(investor__first_name__icontains=request.query_params.get('investor')) |
                        Q(investor__social_reason__icontains=request.query_params.get('investor')) |
                        Q(emitter__last_name__icontains=request.query_params.get('investor')) |
                        Q(emitter__first_name__icontains=request.query_params.get('investor')) |
                        Q(emitter__social_reason__icontains=request.query_params.get('investor'))),
                        opDate__gte=request.query_params.get('startDate'),
                        opDate__lte=request.query_params.get('endDate'),
                        opExpiration__lt=today
                    ).exclude(status=4)
                elif request.query_params.get('status') == '1':
                    today = timezone.now().date()
                    preOperations = PreOperation.objects.filter(
                        (Q(investor__last_name__icontains=request.query_params.get('investor')) |
                        Q(investor__first_name__icontains=request.query_params.get('investor')) |
                        Q(investor__social_reason__icontains=request.query_params.get('investor')) |
                        Q(emitter__last_name__icontains=request.query_params.get('investor')) |
                        Q(emitter__first_name__icontains=request.query_params.get('investor')) |
                        Q(emitter__social_reason__icontains=request.query_params.get('investor'))),
                        opDate__gte=request.query_params.get('startDate'),
                        opDate__lte=request.query_params.get('endDate'),
                        opExpiration__gt=today,
                        status=1
                    )
                else:
                    preOperations = PreOperation.objects.filter(
                        (Q(investor__last_name__icontains=request.query_params.get('investor')) |
                        Q(investor__first_name__icontains=request.query_params.get('investor')) |
                        Q(investor__social_reason__icontains=request.query_params.get('investor')) |
                        Q(emitter__last_name__icontains=request.query_params.get('investor')) |
                        Q(emitter__first_name__icontains=request.query_params.get('investor')) |
                        Q(emitter__social_reason__icontains=request.query_params.get('investor'))),
                        opDate__gte=request.query_params.get('startDate'),
                        opDate__lte=request.query_params.get('endDate'),
                        status__icontains=request.query_params.get('status')
                    )

            elif (request.query_params.get('opId') != '' and request.query_params.get('billId') == '' and request.query_params.get('investor') == '' and request.query_params.get('startDate') !='' and request.query_params.get('endDate') != '' and request.query_params.get('status') != '' and request.query_params.get('mode') =='operations'):
                
                
                if request.query_params.get('status') == '5':
                    # Caso especial para status 5 con fechas y opId
                    today = timezone.now().date()
                    preOperations = PreOperation.objects.filter(
                        opId=request.query_params.get('opId'),
                        opDate__gte=request.query_params.get('startDate'),
                        opDate__lte=request.query_params.get('endDate'),
                        opExpiration__lt=today
                    ).exclude(status=4)
                elif request.query_params.get('status') == '1':
                    today = timezone.now().date()
                    preOperations = PreOperation.objects.filter(
                        opId=request.query_params.get('opId'),
                        opDate__gte=request.query_params.get('startDate'),
                        opDate__lte=request.query_params.get('endDate'),
                        opExpiration__gt=today,
                        status=1
                    )
                else:
                    preOperations = PreOperation.objects.filter(
                        opId=request.query_params.get('opId'),
                        status__icontains=request.query_params.get('status'),
                        opDate__gte=request.query_params.get('startDate'),
                        opDate__lte=request.query_params.get('endDate')
                    )

            elif (request.query_params.get('opId') == '' and request.query_params.get('billId') != '' and request.query_params.get('investor') == '' and request.query_params.get('startDate') !='' and request.query_params.get('endDate') != '' and request.query_params.get('status') != '' and request.query_params.get('mode') =='operations'):
                
                
                if request.query_params.get('status') == '5':
                    # Caso especial para status 5 con fechas y billId
                    today = timezone.now().date()
                    preOperations = PreOperation.objects.filter(
                        bill_id__billId__icontains=request.query_params.get('billId'),
                        opDate__gte=request.query_params.get('startDate'),
                        opDate__lte=request.query_params.get('endDate'),
                        opExpiration__lt=today
                    ).exclude(status=4)
                elif request.query_params.get('status') == '1':
                    today = timezone.now().date()
                    preOperations = PreOperation.objects.filter(
                        bill_id__billId__icontains=request.query_params.get('billId'),
                        opDate__gte=request.query_params.get('startDate'),
                        opDate__lte=request.query_params.get('endDate'),
                        opExpiration__gt=today,
                        status=1
                    )
                else:
                    preOperations = PreOperation.objects.filter(
                        bill_id__billId__icontains=request.query_params.get('billId'),
                        status__icontains=request.query_params.get('status'),
                        opDate__gte=request.query_params.get('startDate'),
                        opDate__lte=request.query_params.get('endDate')
                    )
            elif (request.query_params.get('opId') != '' and request.query_params.get('billId') == '' and request.query_params.get('investor') == '' and request.query_params.get('startDate') == '' and request.query_params.get('endDate') == '' and request.query_params.get('status') == '' ):
                
                preOperations = PreOperation.objects.filter(opId=request.query_params.get('opId'),   status__in=[0, 2])


            elif (request.query_params.get('opId') == '' and request.query_params.get('billId') != '' and request.query_params.get('investor') == '' and request.query_params.get('startDate') == '' and request.query_params.get('endDate') == '' and request.query_params.get('status') == ''):                
                
                preOperations = PreOperation.objects.filter(bill_id__billId__icontains=request.query_params.get('billId'),  status__in=[0, 2])

            elif (request.query_params.get('opId') == '' and request.query_params.get('billId') == '' and request.query_params.get('investor') != '' and request.query_params.get('startDate') == '' and request.query_params.get('endDate') == '' and request.query_params.get('status') == ''):
                
                preOperations = PreOperation.objects.filter(Q(investor__last_name__icontains=request.query_params.get('investor')) |
                                                            Q(investor__first_name__icontains=request.query_params.get('investor')) |
                                                               Q(bill_id__billId__icontains=request.query_params.get('investor')) |
                                                            Q(investor__social_reason__icontains=request.query_params.get('investor')) |
                                                            Q(emitter__last_name__icontains=request.query_params.get('investor')) |
                                                            Q(emitter__first_name__icontains=request.query_params.get('investor')) |
                                                          Q(emitter__social_reason__icontains=request.query_params.get('investor')),  status__in=[0, 2])
            
            elif (request.query_params.get('opId') == '' and request.query_params.get('billId') == '' and request.query_params.get('investor') == '' and request.query_params.get('startDate') != '' and request.query_params.get('endDate') != '' and request.query_params.get('status') == ''):
                
                preOperations = PreOperation.objects.filter(
                    opDate__gte=request.query_params.get('startDate'),
                    opDate__lte=request.query_params.get('endDate'),  status__in=[0, 2]
                )
            elif (request.query_params.get('opId') != '' and request.query_params.get('billId') == '' and request.query_params.get('investor') == '' and request.query_params.get('startDate') != '' and request.query_params.get('endDate') != '' and request.query_params.get('status') == ''):
                
                preOperations = PreOperation.objects.filter(
                    opId=request.query_params.get('opId'),
                    status__lte=4,
                    opDate__gte=request.query_params.get('startDate'),
                    opDate__lte=request.query_params.get('endDate'),  status__in=[0, 2]
                )

            elif (request.query_params.get('opId') == '' and request.query_params.get('billId') != '' and request.query_params.get('investor') == '' and request.query_params.get('startDate') != '' and request.query_params.get('endDate') != '' and request.query_params.get('status') == ''):                
                
                preOperations = PreOperation.objects.filter(
                    bill_id__billId__icontains=request.query_params.get('billId'),
                    opDate__gte=request.query_params.get('startDate'),
                    opDate__lte=request.query_params.get('endDate'),  status__in=[0, 2]
                )

            elif (request.query_params.get('opId') == '' and request.query_params.get('billId') == '' and request.query_params.get('investor') != '' and request.query_params.get('startDate') != '' and request.query_params.get('endDate') != '' and request.query_params.get('status') == ''):
                
                preOperations = PreOperation.objects.filter(
                    
                    Q(investor__last_name__icontains=request.query_params.get('investor')) |
                    Q(investor__first_name__icontains=request.query_params.get('investor')) |
                    Q(investor__social_reason__icontains=request.query_params.get('investor')) |
                    Q(emitter__last_name__icontains=request.query_params.get('investor')) |
                    Q(emitter__first_name__icontains=request.query_params.get('investor')) |
                    Q(emitter__social_reason__icontains=request.query_params.get('investor')),
                    opDate__gte=request.query_params.get('startDate'),
                    opDate__lte=request.query_params.get('endDate'),  status__in=[0, 2]
                )
                
            elif (request.query_params.get('opId') == '' and request.query_params.get('billId') == '' and request.query_params.get('investor') == '' and request.query_params.get('startDate') == '' and request.query_params.get('endDate') == '' and request.query_params.get('status') != ''):
                
                preOperations = PreOperation.objects.filter(
                    
                  status__icontains=request.query_params.get('status')
                )
                
            elif (request.query_params.get('opId') == '' and request.query_params.get('billId') == '' and request.query_params.get('investor') == '' and request.query_params.get('startDate') != '' and request.query_params.get('endDate') != '' and request.query_params.get('status') != ''):
                
                preOperations = PreOperation.objects.filter(
                   opDate__gte=request.query_params.get('startDate'),
                    opDate__lte=request.query_params.get('endDate'), 
                  status__icontains=request.query_params.get('status')
                )
                
            elif (request.query_params.get('opId') == '' and request.query_params.get('billId') == '' and request.query_params.get('investor')  !='' and request.query_params.get('startDate') != '' and request.query_params.get('endDate') != '' and request.query_params.get('status') != ''):
                
                preOperations = PreOperation.objects.filter(
                     Q(investor__last_name__icontains=request.query_params.get('investor')) |
                    Q(investor__first_name__icontains=request.query_params.get('investor')) |
                    Q(investor__social_reason__icontains=request.query_params.get('investor')) |
                    Q(emitter__last_name__icontains=request.query_params.get('investor')) |
                    Q(emitter__first_name__icontains=request.query_params.get('investor')) |
                    Q(emitter__social_reason__icontains=request.query_params.get('investor')),
                   opDate__gte=request.query_params.get('startDate'),
                    opDate__lte=request.query_params.get('endDate'), 
                  status__icontains=request.query_params.get('status')
                )
            elif (request.query_params.get('opId') != '' and request.query_params.get('billId') == '' and request.query_params.get('investor') == '' and request.query_params.get('startDate') =='' and request.query_params.get('endDate') == '' and request.query_params.get('status') != ''):
                
                preOperations = PreOperation.objects.filter(
                  opId=request.query_params.get('opId'),  
                  status__icontains=request.query_params.get('status'),
              
                )   
            elif (request.query_params.get('opId') != '' and request.query_params.get('billId') == '' and request.query_params.get('investor') == '' and request.query_params.get('startDate') !='' and request.query_params.get('endDate') != '' and request.query_params.get('status') != ''):
                
                preOperations = PreOperation.objects.filter(
                  opId=request.query_params.get('opId'),  
                  status__icontains=request.query_params.get('status'),
                  opDate__gte=request.query_params.get('startDate'),
                opDate__lte=request.query_params.get('endDate')
                )
                
            elif (request.query_params.get('opId') == '' and request.query_params.get('billId') != '' and request.query_params.get('investor') == '' and request.query_params.get('startDate') !='' and request.query_params.get('endDate') != '' and request.query_params.get('status') != ''):
                
                preOperations = PreOperation.objects.filter(
                  bill_id__billId__icontains=request.query_params.get('billId'),
                  status__icontains=request.query_params.get('status'),
                  opDate__gte=request.query_params.get('startDate'),
                opDate__lte=request.query_params.get('endDate')
                )
            else:
                
                preOperations = PreOperation.objects.filter(status__in=[0, 2])

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

           # if sum >= 165000:
             #   data['commission'] = sum
            #else:
                #data['commission'] = 165000
                
            data['commission'] = sum    
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







class UploadExcelValidator:
    REQUIRED_FIELDS = [
        "op_id",
        "op_date",
        "emitter_name",
        "emitter_id",
        "emitter_broker_name",
        "emitter_broker_id",
        "payer_name",
        "payer_id",
        "bill_number",
        "bill_id",
        "bill_balance",
        "bill_fraction",
        "investor_name",
        "investor_id",
        "investor_account",
        "fecha_probable",
        "fecha_fin",
        "valor_futuro",
        "porcentaje_descuento",
        "tasa_descuento",
        "tasa_inversionista",
    ]

    CALC_REQUIRED_FIELDS = [
        "valor_futuro",
        "porcentaje_descuento",
        "tasa_descuento",
        "tasa_inversionista",
        "op_date",
        "fecha_fin",
    ]

    def __init__(self, references, calculator, upload_context=None):
        self.references = references
        self.calculator = calculator
        self.upload_context = upload_context or {}

    def _add_context_errors(self, parsed_rows):
        """
        Valida que el Excel pertenezca a la operación armada en el front.
        """
        if not self.upload_context:
            return {}

        errors_by_row = defaultdict(list)

        expected_op_date = self.upload_context.get("opDate")
        expected_emitter_id = str(self.upload_context.get("emitterId") or "").strip()
        expected_emitter_broker_id = str(self.upload_context.get("emitterBrokerId") or "").strip()
        expected_payer_id = str(self.upload_context.get("payerId") or "").strip()

        expected_rows = self.upload_context.get("rows") or []

        excel_op_dates = {
            row.get("op_date").isoformat() if row.get("op_date") else None
            for row in parsed_rows
        }
        excel_emitter_ids = {
            str(row.get("emitter_id") or "").strip()
            for row in parsed_rows
        }
        excel_emitter_broker_ids = {
            str(row.get("emitter_broker_id") or "").strip()
            for row in parsed_rows
        }
        excel_payer_ids = {
            str(row.get("payer_id") or "").strip()
            for row in parsed_rows
        }

        if expected_op_date and excel_op_dates != {expected_op_date}:
            for row in parsed_rows:
                errors_by_row[row["row_number"]].append({
                    "field": "op_date",
                    "message": "La fecha de operación del Excel no coincide con la operación actual",
                })

        if expected_emitter_id and excel_emitter_ids != {expected_emitter_id}:
            for row in parsed_rows:
                errors_by_row[row["row_number"]].append({
                    "field": "emitter_id",
                    "message": "El emisor del Excel no coincide con el emisor seleccionado",
                })

        if expected_emitter_broker_id and excel_emitter_broker_ids != {expected_emitter_broker_id}:
            for row in parsed_rows:
                errors_by_row[row["row_number"]].append({
                    "field": "emitter_broker_id",
                    "message": "El corredor del emisor del Excel no coincide con el seleccionado",
                })

        if expected_payer_id and excel_payer_ids != {expected_payer_id}:
            for row in parsed_rows:
                errors_by_row[row["row_number"]].append({
                    "field": "payer_id",
                    "message": "El pagador del Excel no coincide con el pagador seleccionado",
                })

        expected_pairs = {
            (
                str(item.get("billId") or "").strip(),
                int(item.get("billFraction") or 0),
                str(item.get("investorId") or "").strip(),
                str(item.get("investorAccount") or "").strip(),
            )
            for item in expected_rows
        }

        excel_pairs = {
            (
                str(row.get("bill_id") or "").strip(),
                int(row.get("bill_fraction") or 0),
                str(row.get("investor_id") or "").strip(),
                str(row.get("investor_account") or "").strip(),
            )
            for row in parsed_rows
        }

        if expected_pairs and excel_pairs != expected_pairs:
            unexpected_pairs = excel_pairs - expected_pairs
            missing_pairs = expected_pairs - excel_pairs

            for row in parsed_rows:
                current_pair = (
                    str(row.get("bill_id") or "").strip(),
                    int(row.get("bill_fraction") or 0),
                    str(row.get("investor_id") or "").strip(),
                    str(row.get("investor_account") or "").strip(),
                )

                if current_pair in unexpected_pairs:
                    errors_by_row[row["row_number"]].append({
                        "field": "operation_context",
                        "message": "Esta fila no pertenece al lote actual de la operación",
                    })

            if missing_pairs:
                for row in parsed_rows:
                    errors_by_row[row["row_number"]].append({
                        "field": "operation_context",
                        "message": "Faltan filas del lote actual en el Excel cargado",
                    })
                    break

        return errors_by_row

    def validate_rows(self, parsed_rows):
        grouped_by_bill = defaultdict(list)
        for row in parsed_rows:
            bill_id = str(row.get("bill_id")) if row.get("bill_id") else None
            if bill_id:
                grouped_by_bill[bill_id].append(row)

        context_errors_by_row = self._add_context_errors(parsed_rows)

        validated = []

        for row in parsed_rows:
            field_errors = {}
            errors = []

            def add_error(field, message):
                field_errors[field] = True
                errors.append({"field": field, "message": message})

            for field in self.REQUIRED_FIELDS:
                if row.get(field) in [None, ""]:
                    add_error(field, "Este campo es obligatorio")

            for ctx_error in context_errors_by_row.get(row["row_number"], []):
                add_error(ctx_error["field"], ctx_error["message"])

            emitter = self.references["clients_by_id"].get(str(row.get("emitter_id")))
            payer = self.references["clients_by_id"].get(str(row.get("payer_id")))
            investor = self.references["clients_by_id"].get(str(row.get("investor_id")))
            bill = self.references["bills_by_id"].get(str(row.get("bill_id")))
            emitter_broker = self.references["brokers_by_id"].get(str(row.get("emitter_broker_id")))
            account = self.references["accounts_by_number"].get(str(row.get("investor_account")).strip())
            risk_profile = self.references["risk_profile_by_client_id"].get(str(row.get("investor_id")))
            investor_broker_info = self.references["investor_broker_by_investor_id"].get(
                str(row.get("investor_id")),
                {},
            )

            if row.get("emitter_id") and not emitter:
                add_error("emitter_id", "El emisor no existe")

            if row.get("payer_id") and not payer:
                add_error("payer_id", "El pagador no existe")

            if row.get("investor_id") and not investor:
                add_error("investor_id", "El inversionista no existe")

            if row.get("bill_id") and not bill:
                add_error("bill_id", "La factura no existe")

            if row.get("emitter_broker_id") and not emitter_broker:
                add_error("emitter_broker_id", "El corredor del emisor no existe")

            if row.get("investor_account") and not account:
                add_error("investor_account", "La cuenta del inversionista no existe")

            if investor and account and str(getattr(account, "client_id", "")) != str(investor.id):
                add_error("investor_account", "La cuenta no pertenece al inversionista")

            if investor and not investor_broker_info.get("broker_id"):
                add_error("investor_id", "El inversionista no tiene corredor asociado")

            if bill and emitter and hasattr(bill, "emitter_id"):
                if str(bill.emitter_id) != str(emitter.id):
                    add_error("bill_id", "La factura no pertenece al emisor")

            if bill and payer and hasattr(bill, "payer_id"):
                if str(bill.payer_id) != str(payer.id):
                    add_error("bill_id", "La factura no pertenece al pagador")

            bill_id = str(row.get("bill_id")) if row.get("bill_id") else None
            if bill_id and row.get("bill_fraction") is not None:
                grouped_rows = sorted(
                    grouped_by_bill[bill_id],
                    key=lambda x: x.get("bill_fraction") or 0
                )

                expected_start = self.references["next_fraction_by_bill"].get(bill_id, 0)
                if expected_start == 0:
                    expected_start = 1

                expected_sequence = list(range(expected_start, expected_start + len(grouped_rows)))
                actual_sequence = [r.get("bill_fraction") for r in grouped_rows]

                if actual_sequence != expected_sequence:
                    add_error(
                        "bill_fraction",
                        f"Las fracciones deben ser consecutivas: {expected_sequence}"
                    )

            valor_futuro = row.get("valor_futuro")
            bill_balance = row.get("bill_balance")

            if valor_futuro is not None and bill_balance is not None:
                if valor_futuro <= 0:
                    add_error("valor_futuro", "El valor futuro debe ser mayor a 0")
                if valor_futuro > bill_balance:
                    add_error("valor_futuro", "El valor futuro no puede ser mayor al saldo")

            if bill_id:
                total_future = sum((r.get("valor_futuro") or 0) for r in grouped_by_bill[bill_id])
                current_balance = row.get("bill_balance") or 0
                if total_future > current_balance:
                    add_error(
                        "valor_futuro",
                        "La suma del valor futuro de las fracciones no puede superar el saldo"
                    )

            porcentaje_descuento = row.get("porcentaje_descuento")
            if porcentaje_descuento is not None:
                if porcentaje_descuento < 0:
                    add_error("porcentaje_descuento", "El % descuento no puede ser menor a 0")
                if porcentaje_descuento > 100:
                    add_error("porcentaje_descuento", "El % descuento no puede ser mayor a 100")

            tasa_desc = row.get("tasa_descuento")
            if tasa_desc is not None:
                if tasa_desc < 0:
                    add_error("tasa_descuento", "La tasa de descuento no puede ser menor a 0")
                if tasa_desc > 100:
                    add_error("tasa_descuento", "La tasa de descuento no puede ser mayor a 100")

            tasa_inv = row.get("tasa_inversionista")
            if tasa_inv is not None:
                if tasa_inv < 0:
                    add_error("tasa_inversionista", "La tasa inversionista no puede ser menor a 0")
                if tasa_inv > 100:
                    add_error("tasa_inversionista", "La tasa inversionista no puede ser mayor a 100")

            if tasa_desc is not None and tasa_inv is not None:
                if tasa_desc < tasa_inv:
                    add_error(
                        "tasa_descuento",
                        "La tasa de descuento no puede ser menor a la tasa inversionista"
                    )

            fecha_probable = row.get("fecha_probable")
            fecha_fin = row.get("fecha_fin")
            op_date = row.get("op_date")

            if fecha_probable and op_date and fecha_probable < op_date:
                add_error(
                    "fecha_probable",
                    "La fecha probable no puede ser menor a la fecha de operación"
                )

            if fecha_fin and fecha_probable and fecha_fin < fecha_probable:
                add_error(
                    "fecha_fin",
                    "La fecha fin no puede ser menor a la fecha probable"
                )

            calculated_payload = {}
            can_calculate = all(row.get(field) not in [None, ""] for field in self.CALC_REQUIRED_FIELDS)

            if can_calculate:
                try:
                    apply_gm = bool(getattr(risk_profile, "gmf", False)) if risk_profile else False

                    calculated_payload = self.calculator.calculate(row, apply_gm=apply_gm)
                    calculated_payload["applyGm"] = apply_gm

                    valor_nominal = calculated_payload.get("valorNominal")
                    if valor_nominal is not None and valor_futuro is not None and valor_nominal > valor_futuro:
                        add_error(
                            "valor_nominal",
                            "El valor nominal no puede ser mayor al valor futuro"
                        )

                    if account:
                        required_balance = (
                            calculated_payload.get("presentValueInvestor", 0) +
                            calculated_payload.get("GM", 0)
                        )
                        account_balance = float(getattr(account, "balance", 0) or 0)
                        calculated_payload["insufficientAccountBalance"] = required_balance > account_balance
                        calculated_payload["accountBalance"] = account_balance

                    calculated_payload["investorBrokerId"] = investor_broker_info.get("broker_id")
                    calculated_payload["investorBrokerName"] = investor_broker_info.get("broker_name", "")

                except Exception as exc:
                    add_error("calculation", f"No se pudo calcular la fila: {str(exc)}")

            validated.append({
                **row,
                "field_errors": field_errors,
                "errors": errors,
                "has_errors": len(errors) > 0,
                "calculated_payload": calculated_payload,
            })

        return validated        
class UploadExcel(APIView):
    def post(self, request):
        excel_file = request.FILES.get("uploadExcel")
        if not excel_file:
            return Response(
                {"message": "No se recibió el archivo uploadExcel"},
                status=status.HTTP_400_BAD_REQUEST
            )

        raw_context = request.data.get("context")
        upload_context = None

        if raw_context:
            try:
                upload_context = json.loads(raw_context)
            except Exception:
                return Response(
                    {"message": "El contexto de carga es inválido"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        try:
            parser = UploadExcelParser()
            parsed_rows = parser.parse(excel_file)
        except ValueError as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response(
                {"message": "No fue posible leer el archivo Excel"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not parsed_rows:
            return Response(
                {"message": "El archivo no contiene filas válidas"},
                status=status.HTTP_400_BAD_REQUEST
            )

        references = UploadExcelReferenceResolver().resolve(parsed_rows)
        calculator = UploadExcelCalculator()
        validator = UploadExcelValidator(
            references,
            calculator,
            upload_context=upload_context,
        )

        validated_rows = validator.validate_rows(parsed_rows)
        response_data = UploadExcelResponseBuilder().build(validated_rows)

        if response_data.get("errorCount", 0) > 0:
            all_errors = [
                error
                for row in response_data.get("rows", [])
                for error in row.get("errors", [])
            ]

            has_context_error = any(
                error.get("field") in [
                    "operation_context",
                    "context_op_date",
                    "context_emitter_id",
                    "context_emitter_broker_id",
                    "context_payer_id",
                ]
                for error in all_errors
            )

            if has_context_error:
                response_data["message"] = (
                    "El Excel no corresponde a la operación actual. "
                    "Verifique emisor, pagador, facturas, fracciones, inversionistas y cuentas."
                )
            else:
                response_data["message"] = (
                    "El Excel contiene errores en los datos. "
                    "Revise los valores resaltados en la tabla."
                )

        return Response(response_data, status=status.HTTP_200_OK) 
class RegisterOperationFromUpload(APIView):
    @transaction.atomic
    def post(self, request):
        normalized_rows = request.data.get("rows", [])
        op_type_id = request.data.get("opTypeId")

        if not normalized_rows or not isinstance(normalized_rows, list):
            return Response(
                {"message": "Debe enviar la lista de rows"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not op_type_id:
            return Response(
                {"message": "El tipo de operación es requerido"},
                status=status.HTTP_400_BAD_REQUEST
            )

        rows_with_errors = [row for row in normalized_rows if row.get("hasErrors")]
        if rows_with_errors:
            return Response(
                {"message": "Existen filas con errores. No se puede registrar la operación."},
                status=status.HTTP_400_BAD_REQUEST
            )

        first_row = normalized_rows[0]
        requested_op_id = first_row.get("opId")

        if requested_op_id is None:
            return Response(
                {"message": "El opId es requerido"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            requested_op_id = int(requested_op_id)
        except (TypeError, ValueError):
            return Response(
                {"message": "El opId debe ser numérico"},
                status=status.HTTP_400_BAD_REQUEST
            )

        with connection.cursor() as cursor:
            cursor.execute("SELECT GET_LOCK(%s, %s)", ["register_massive_operation_opid", 10])
            result = cursor.fetchone()

            if not result or result[0] != 1:
                return Response(
                    {"message": "No fue posible asegurar el consecutivo del opId. Intente nuevamente."},
                    status=status.HTTP_409_CONFLICT
                )

        last_op_id = (
            PreOperation.objects
            .aggregate(max_op_id=Max("opId"))
            .get("max_op_id")
        ) or 0

        final_op_id = max(requested_op_id, last_op_id + 1)
        op_id_changed = final_op_id != requested_op_id

        created_ids = []

        for index, row in enumerate(normalized_rows):
            calculated = row.get("calculated", {})

            try:
                account = Account.objects.get(account_number=row["clientAccountNumber"])
            except Account.DoesNotExist:
                transaction.set_rollback(True)
                return Response(
                    {"message": f"No existe la cuenta {row['clientAccountNumber']}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                bill = Bill.objects.get(id=row["billId"])
            except Bill.DoesNotExist:
                transaction.set_rollback(True)
                return Response(
                    {"message": f"No existe la factura {row['billId']}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            last_fraction = (
                PreOperation.objects
                .filter(bill_id=row["billId"])
                .order_by("-billFraction")
                .values_list("billFraction", flat=True)
                .first()
            ) or 0

            if row["billFraction"] <= last_fraction:
                transaction.set_rollback(True)
                return Response(
                    {"message": f"La fracción {row['billFraction']} ya no es válida para la factura {row['billId']}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            payload = {
                "opId": final_op_id,
                "opType": op_type_id,
                "opDate": row["opDate"],
                "applyGm": row.get("applyGm", False),

                "emitter": row["emitterId"],
                "payer": row["payerId"],
                "investor": row["investorId"],
                "clientAccount": account.id,
                "bill": bill.id,

                "billFraction": row["billFraction"],
                "DateBill": getattr(bill, "dateBill", None),
                "DateExpiration": getattr(bill, "expirationDate", None),
                "probableDate": row["fechaProbable"],
                "opExpiration": calculated.get("opExpiration"),

                "amount": row["valorFuturo"],
                "payedPercent": row["porcentajeDescuento"],
                "payedAmount": calculated.get("valorNominal"),

                "discountTax": row["tasaDescuento"],
                "investorTax": row["tasaInversionista"],

                "emitterBroker": row["emitterBrokerId"],
                "investorBroker": row["investorBrokerId"],

                "operationDays": calculated.get("operationDays"),
                "presentValueInvestor": calculated.get("presentValueInvestor"),
                "presentValueSF": calculated.get("presentValueSF"),
                "investorProfit": calculated.get("investorProfit"),
                "commissionSF": calculated.get("commissionSF"),
                "GM": calculated.get("GM"),

                "status": 0,
                "isRebuy": False,
                "insufficientAccountBalance": calculated.get("insufficientAccountBalance", False),
            }

            serializer = PreOperationSerializer(
                data=payload,
                context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()

            created_ids.append(instance.id)

            transaction.on_commit(
                lambda instance=instance, index=index, payload=payload, bill=bill: create_operation_log(
                    source="REGISTER_FROM_UPLOAD",
                    action="CREATE_ROW",
                    status="SUCCESS",
                    message=f"Fila {index} registrada correctamente",
                    op_id=instance.opId,
                    pre_operation=instance,
                    row_index=index,
                    request_payload=payload,
                    response_payload={"id": str(instance.id)},
                    bill_id_ref=str(bill.id),
                    user=request.user,
                )
            )

        
        
        
        
        transaction.on_commit(lambda: create_operation_log(
            source="REGISTER_FROM_UPLOAD",
            action="REGISTER_OPERATION",
            status="SUCCESS",
            message=(
                f"Operación registrada correctamente. El opId fue ajustado de {requested_op_id} a {final_op_id}."
                if op_id_changed
                else "Operación registrada correctamente"
            ),
            op_id=final_op_id,
            response_payload={
                "createdCount": len(created_ids),
                "ids": [str(x) for x in created_ids],
                "requested": requested_op_id,
                "final": final_op_id,
                "changed": op_id_changed,
            },
            user=request.user,
        ))


        return Response(
            {
                "success": True,
                "message": (
                    f"Operación registrada correctamente. "
                    f"El opId fue ajustado de {requested_op_id} a {final_op_id}."
                    if op_id_changed
                    else "Operación registrada correctamente"
                ),
                "createdCount": len(created_ids),
                "ids": created_ids,
                "opIdInfo": {
                    "requested": requested_op_id,
                    "final": final_op_id,
                    "changed": op_id_changed,
                },
            },
            status=status.HTTP_201_CREATED
        )
        
        
def build_client_name(client):
    if not client:
        return ""
    if getattr(client, "social_reason", None):
        return client.social_reason
    return f"{client.first_name or ''} {client.last_name or ''}".strip()


class MassiveOperationReceiptPDFAV(APIView):

    def get(self, request, op_id):
        # ⏱️ 1) medir query real
        t0 = time.perf_counter()
        operations = list(
            PreOperation.objects
            .select_related("bill", "emitter", "payer", "investor", "user_created_at")
            .filter(opId=op_id)
            .order_by("id")
        )
        logger.debug(f"⏱️ query: {time.perf_counter() - t0:.4f}s")

        if not operations:
            return HttpResponse(
                "No existe una operación masiva con ese opId",
                status=status.HTTP_404_NOT_FOUND,
            )

        first = operations[0]

        total_registros = len(operations)
        total_days = Decimal("0")
        total_discount_tax = Decimal("0")
        total_investor_tax = Decimal("0")

        detail_rows = []

        for op in operations:
            days = Decimal(str(op.operationDays or 0))
            discount_tax = Decimal(str(op.discountTax or 0))
            investor_tax = Decimal(str(op.investorTax or 0))

            total_days += days
            total_discount_tax += discount_tax
            total_investor_tax += investor_tax

            bill_number = getattr(op.bill, "billId", None) or str(op.bill_id)

            if op.billFraction and int(op.billFraction) > 0:
                bill_label = f"{bill_number}-{op.billFraction}"
            else:
                bill_label = bill_number

            detail_rows.append({
                "factura": bill_label,
                "emisor": build_client_name(op.emitter),
                "pagador": build_client_name(op.payer),
                "vencimiento": op.DateExpiration,
                "dias": int(op.operationDays or 0),
                "tasa_desc": float(op.discountTax or 0),
                "saldo_factura": float(op.amount or 0),
            })

        avg_days = float(total_days / total_registros) if total_registros else 0
        avg_discount_tax = float(total_discount_tax / total_registros) if total_registros else 0
        avg_investor_tax = float(total_investor_tax / total_registros) if total_registros else 0

        created_by = "Usuario Smart Evolution"
        if getattr(first, "user_created_at", None):
            created_by = (
                getattr(first.user_created_at, "name", None)
                or getattr(first.user_created_at, "first_name", None)
                or getattr(first.user_created_at, "email", None)
                or created_by
            )
            
            email= getattr(first.user_created_at, "email", None)

        context = {
            "receipt": {
                "op_id": first.opId,
                "generated_at": timezone.now(),
                "created_by": created_by,
                "apellido": getattr(first.user_created_at, "last_name", None),
                "email": email,
                "operation_date": first.opDate,
                "total_registros": total_registros,
                "avg_days": avg_days,
                "avg_discount_tax": avg_discount_tax,
                "avg_investor_tax": avg_investor_tax,
                "detail_rows": detail_rows,
                "note": (
                    f"El promedio de días se calculó con base en la diferencia "
                    f"entre la fecha de inicio ({first.opDate}) y la fecha fin de cada título. "
                    f"Los valores de tasa son promedios simples de la carga masiva."
                ),
            }
        }

        template = get_template("massive_operation_receipt.html")

        # ⏱️ 2) medir render html
        t1 = time.perf_counter()
        html_content = template.render(context)
        logger.debug(f"⏱️ render html: {time.perf_counter() - t1:.4f}s")

        # ⏱️ 3) medir generación pdf
        t2 = time.perf_counter()
        payload = {
                "html": html_content,
                "pdf_type": "massive_operation_receipt",
            }

        parse_base64 = pdfToBase64(payload)
        logger.debug(f"⏱️ pdf: {time.perf_counter() - t2:.4f}s")

        if "pdf" not in parse_base64:
            return HttpResponse(
                "No fue posible generar el PDF",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        pdf_bytes = base64.b64decode(parse_base64["pdf"])

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="Comprobante_OP_{first.opId}_{timezone.now().strftime("%Y-%m-%d_%H-%M-%S")}.pdf"'
        )
        return response
    
class BillsByOpId(APIView):
    def get(self, request, pk):
        try:
            operations = (
                PreOperation.objects
                .filter(opId=pk, bill__isnull=False,status=1)
                .select_related("bill", "investor", "clientAccount")
            )

            data = []
            for op in operations:
                bill_data = BillSerializer(op.bill).data

                investor_name = ""
                if op.investor:
                    if getattr(op.investor, "first_name", None):
                        investor_name = f"{op.investor.first_name} {op.investor.last_name}"
                    else:
                        investor_name = op.investor.social_reason or ""

                investor_account = ""
                if op.clientAccount:
                    investor_account = (
                        getattr(op.clientAccount, "account_number", None)
                        or getattr(op.clientAccount, "number", None)
                        or ""
                    )

                bill_data["investorId"] = str(op.investor_id) if op.investor_id else None
                bill_data["investorName"] = investor_name
                bill_data["investorAccountId"] = str(op.clientAccount_id) if op.clientAccount_id else None
                bill_data["investorAccount"] = investor_account
                bill_data["valorNominal"] = op.payedAmount
                bill_data["valorFuturo"] = op.amount
                bill_data["billFraction"] = op.billFraction

                data.append(bill_data)

            return response({
                "error": False,
                "data": data
            }, 200)

        except Exception as e:
            return response(
                {"error": True, "message": str(e)},
                e.status_code if hasattr(e, "status_code") else 500
            )
            
def get_draft_queryset(request):
    return MassiveOperationDraft.objects.filter(
        state=True,
        user_created_at=request.user,
        status__in=[
            MassiveOperationDraft.STATUS_DRAFT,
            MassiveOperationDraft.STATUS_READY_FOR_EXCEL,
        ],
    )

class MassiveOperationDraftAV(APIView):
    def get(self, request):
        qs = get_draft_queryset(request)

        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        qs = (
            qs.order_by("-updated_at", "-created_at")
            .values(
                "id", "opId", "opDate", "opType_id", "emitter_id",
                "payer_id", "emitterBroker_id", "currentStep", "status",
                "expiresAt", "registeredOpId", "created_at", "updated_at",
                "metadata",
            )[:50]
        )

        data = []
        for item in qs:
            metadata = item.get("metadata") or {}
            data.append({
                "id": item["id"],
                "opId": item["opId"],
                "opDate": item["opDate"],
                "opTypeId": item["opType_id"],
                "emitterId": item["emitter_id"],
                "payerId": item["payer_id"],
                "emitterBrokerId": item["emitterBroker_id"],
                "currentStep": item["currentStep"],
                "status": item["status"],
                "expiresAt": item["expiresAt"],
                "registeredOpId": item["registeredOpId"],
                "created_at": item["created_at"],
                "updated_at": item["updated_at"],
                "metadata": metadata,
                "selectedBillsCount": metadata.get("selectedBillsCount", 0),
                "assignmentsCount": metadata.get("assignmentsCount", 0),
            })

        return Response({"error": False, "data": data}, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data.copy()

        if not data.get("expiresAt"):
            data["expiresAt"] = timezone.now() + timedelta(days=10)

        serializer = MassiveOperationDraftSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        draft = serializer.save(
            user_created_at=request.user,
            user_updated_at=request.user,
        )

        return Response({
            "error": False,
            "message": "Borrador creado correctamente",
            "data": MassiveOperationDraftSerializer(draft).data,
        }, status=status.HTTP_201_CREATED)
class MassiveOperationDraftDetailAV(APIView):
    def get_object(self, request, pk):
        return MassiveOperationDraft.objects.get(
            id=pk,
            state=True,
            user_created_at=request.user,
        )

    def get(self, request, pk):
        draft = self.get_object(request, pk)
        serializer = MassiveOperationDraftSerializer(draft)

        return Response({
            "error": False,
            "data": serializer.data,
        }, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        draft = self.get_object(request, pk)

        if draft.status == MassiveOperationDraft.STATUS_REGISTERED:
            return Response({
                "error": True,
                "message": "No se puede modificar un borrador ya registrado.",
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = MassiveOperationDraftSerializer(
            draft,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        draft = serializer.save(
            user_updated_at=request.user,
            updated_at=timezone.now(),
            expiresAt=timezone.now() + timedelta(days=10),
        )

        return Response({
            "error": False,
            "message": "Borrador actualizado correctamente",
            "data": MassiveOperationDraftSerializer(draft).data,
        }, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        draft = self.get_object(request, pk)
        draft.state = False
        draft.status = MassiveOperationDraft.STATUS_CANCELLED
        draft.user_updated_at = request.user
        draft.updated_at = timezone.now()
        draft.save()

        return Response({
            "error": False,
            "message": "Borrador eliminado correctamente",
        }, status=status.HTTP_200_OK)
        
        
class MassiveOperationDraftValidateAV(APIView):
    def post(self, request, pk):
        try:
            draft = MassiveOperationDraft.objects.get(
                id=pk,
                state=True,
                user_created_at=request.user,
            )
        except MassiveOperationDraft.DoesNotExist:
            return Response({
                "error": True,
                "message": "Borrador no encontrado.",
            }, status=status.HTTP_404_NOT_FOUND)

        conflicts = []

        if draft.expiresAt and draft.expiresAt < timezone.now():
            conflicts.append({
                "field": "expiresAt",
                "message": "El borrador expiró. Debe crear una nueva operación.",
            })

        selected_bills = draft.selectedBills or []
        investor_assignments = draft.investorAssignments or []

        def get_bill_uuid(item):
            return str(
                item.get("billUniqueId")
                or item.get("bill_uuid")
                or item.get("billUuid")
                or item.get("billPk")
                or item.get("bill_id_uuid")
                or item.get("id")
                or ""
            ).strip()

        def get_bill_label(item):
            return str(
                item.get("billId")
                or item.get("billCode")
                or item.get("billNumber")
                or get_bill_uuid(item)
                or ""
            ).strip()

        def get_account_number(item):
            selected_account = item.get("selectedAccount") or {}
            return str(
                selected_account.get("account_number")
                or selected_account.get("accountNumber")
                or selected_account.get("number")
                or item.get("investorAccount")
                or ""
            ).strip()

        bill_uuids = {
            get_bill_uuid(item)
            for item in selected_bills
            if get_bill_uuid(item)
        }

        assignment_bill_uuids = {
            get_bill_uuid(item)
            for item in investor_assignments
            if get_bill_uuid(item)
        }

        all_bill_uuids = bill_uuids.union(assignment_bill_uuids)

        bills = Bill.objects.filter(id__in=all_bill_uuids)
        bills_by_id = {str(b.id): b for b in bills}

        draft_emitter_document = str(
            getattr(draft.emitter, "document_number", None)
            or getattr(draft.emitter, "nit", None)
            or getattr(draft.emitter, "identification", None)
            or ""
        ).strip()

        draft_payer_document = str(
            getattr(draft.payer, "document_number", None)
            or getattr(draft.payer, "nit", None)
            or getattr(draft.payer, "identification", None)
            or ""
        ).strip()

        for item in selected_bills:
            bill_uuid = get_bill_uuid(item)
            bill_label = get_bill_label(item)

            if not bill_uuid:
                conflicts.append({
                    "field": "bill",
                    "billId": bill_label,
                    "message": "La factura no tiene UUID válido en el borrador.",
                })
                continue

            bill = bills_by_id.get(bill_uuid)

            if not bill:
                conflicts.append({
                    "field": "bill",
                    "billId": bill_label,
                    "message": "La factura ya no existe.",
                })
                continue

            bill_emitter_document = str(getattr(bill, "emitterId", "") or "").strip()
            bill_payer_document = str(getattr(bill, "payerId", "") or "").strip()

            if draft_emitter_document and bill_emitter_document != draft_emitter_document:
                conflicts.append({
                    "field": "bill",
                    "billId": bill_label,
                    "message": "La factura ya no pertenece al emisor del borrador.",
                })

            if draft_payer_document and bill_payer_document != draft_payer_document:
                conflicts.append({
                    "field": "bill",
                    "billId": bill_label,
                    "message": "La factura ya no pertenece al pagador del borrador.",
                })

        investor_ids = {
            str(item.get("investorId") or "").strip()
            for item in investor_assignments
            if item.get("investorId")
        }

        account_ids = {
            str(item.get("accountId") or "").strip()
            for item in investor_assignments
            if item.get("accountId")
        }

        account_numbers = {
            get_account_number(item)
            for item in investor_assignments
            if get_account_number(item)
        }

        investors = Client.objects.filter(id__in=investor_ids)
        investors_by_id = {str(i.id): i for i in investors}

        accounts_by_id = {
            str(a.id): a
            for a in Account.objects.filter(id__in=account_ids)
        }

        accounts_by_number = {
            str(a.account_number).strip(): a
            for a in Account.objects.filter(account_number__in=account_numbers)
            if a.account_number
        }

        for item in investor_assignments:
            bill_uuid = get_bill_uuid(item)
            bill_label = get_bill_label(item)

            fraction = int(item.get("fraction") or item.get("billFraction") or 0)

            investor_id = str(item.get("investorId") or "").strip()
            account_id = str(item.get("accountId") or "").strip()
            account_number = get_account_number(item)

            if investor_id and investor_id not in investors_by_id:
                conflicts.append({
                    "field": "investor",
                    "investorId": investor_id,
                    "message": "El inversionista ya no existe.",
                })

            account = None

            if account_id:
                account = accounts_by_id.get(account_id)

            if not account and account_number:
                account = accounts_by_number.get(account_number)

            if not account:
                if account_id or account_number:
                    conflicts.append({
                        "field": "account",
                        "accountId": account_id,
                        "accountNumber": account_number,
                        "message": "La cuenta del inversionista ya no existe.",
                    })
            elif investor_id and str(account.client_id) != investor_id:
                conflicts.append({
                    "field": "account",
                    "accountId": str(account.id),
                    "accountNumber": str(account.account_number),
                    "message": "La cuenta ya no pertenece al inversionista.",
                })

            if bill_uuid:
                last_fraction = (
                    PreOperation.objects
                    .filter(bill_id=bill_uuid)
                    .aggregate(max_fraction=Max("billFraction"))
                    .get("max_fraction")
                ) or 0

                if fraction and fraction <= last_fraction:
                    conflicts.append({
                        "field": "billFraction",
                        "billId": bill_label,
                        "fraction": fraction,
                        "message": "La fracción ya no está disponible para esta factura.",
                    })

        is_valid = len(conflicts) == 0

        return Response({
            "error": not is_valid,
            "valid": is_valid,
            "message": (
                "El borrador está vigente."
                if is_valid
                else "El borrador tiene conflictos y debe ser revisado."
            ),
            "conflicts": conflicts,
            "data": MassiveOperationDraftSerializer(draft).data,
        }, status=status.HTTP_200_OK)
class MassiveOperationDraftMarkRegisteredAV(APIView):
    def post(self, request, pk):
        try:
            draft = MassiveOperationDraft.objects.get(
                id=pk,
                state=True,
                user_created_at=request.user,
            )
        except MassiveOperationDraft.DoesNotExist:
            return Response({
                "error": True,
                "message": "Borrador no encontrado.",
            }, status=status.HTTP_404_NOT_FOUND)

        registered_op_id = request.data.get("registeredOpId")

        draft.status = MassiveOperationDraft.STATUS_REGISTERED
        draft.registeredOpId = registered_op_id
        draft.user_updated_at = request.user
        draft.updated_at = timezone.now()
        draft.save()

        return Response({
            "error": False,
            "message": "Borrador marcado como registrado.",
            "data": MassiveOperationDraftSerializer(draft).data,
        }, status=status.HTTP_200_OK)