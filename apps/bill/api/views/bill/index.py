from django.db.models import Q
# Serializers
from apps.bill.api.serializers.index import BillSerializer, BillReadOnlySerializer, BillEventReadOnlySerializer,BillCreationSerializer
from apps.operation.api.serializers.index import PreOperationReadOnlySerializer
# Models
from apps.bill.models import Bill
from apps.client.models import Client
from apps.operation.models import PreOperation
# Utils
from apps.base.utils.index import response, BaseAV, gen_uuid
from apps.bill.utils.index import parseBill, parseCreditNote
from apps.base.decorators.index import checkRole
from base64 import b64decode
import os
import logging

import uuid

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
##comentario2

class BillCreationManualAV(BaseAV):
    @checkRole(['admin','third'])
    def post(self, request):
        try:
            logger.debug(f'Datos recibidos: {request.data}')
            
            # Pasar el contexto con el request al serializer
            serializer = BillCreationSerializer(
                data=request.data,
                context={'request': request}  # ¡Esto es lo que faltaba!
            )
            
            if not serializer.is_valid():
                return response({
                    'error': True,
                    'message': 'Datos inválidos',
                    'details': serializer.errors
                }, 400)
            
            # Crear la factura
            bill = serializer.save()
            
            return response({
                'error': False,
                'message': 'Factura creada exitosamente',
                'billId': bill.billId,
                'uuid': str(bill.id)
            }, 201)
            
        except Exception as e:
            logger.error(f'Error al crear factura: {str(e)}')
            return response({
                'error': True,
                'message': str(e)
            }, 500)
        
class BillAV(BaseAV):

    @checkRole(['admin','third'])
    def post(self, request):
        try:
            data = []
            failedBills = []

            
            

            for x in request.data['bills']:
               

                # Validación del 'integrationCode'
                if 'integrationCode' in x:
                    
                    if x['integrationCode'] != "" or x['integrationCode'] is not None:
                        if x['cufe'] is None or x['cufe'] == "":
                            failedBills.append({
                                'bill': x,
                                'error': 'Factura sin cufe'
                            })
                            logger.warning(f"Factura sin CUFE: {x}")
                        else:
                            # Verifica si la factura ya está registrada por su CUFE
                            checkBill = Bill.objects.filter(cufe=x['cufe'])
                            if checkBill.exists():
                                failedBills.append({
                                    'bill': x,
                                    'error': 'Factura con cufe registrado'
                                })
                                logger.warning(f"Factura con CUFE ya registrado: {x}")
                            else:
                                data.append(x)
                               
                    else:
                        data.append(x)
                        
                else:
                    data.append(x)
                    

            if len(failedBills) > 0:
                logger.warning(f"Algunas facturas presentan errores: {failedBills}")
                return response({'error': False, 'message': 'Algunas facturas presentan errores', 'bills': data,
                                 'failedBills': failedBills}, 400)
            else:
                # Guardar facturas
                for row in data:
                    # Verificar y registrar notas de crédito
                    credit_notes = row.get('creditNotes', [])
                    request.data['creditNotes'] = credit_notes
                   

                    # Verificar y registrar eventos
                    events = row.get('events', [])
                    request.data['events'] = events
                    

                    # Validar formato de fechas
                    if 'dateBill' in row:
                        
                        if 'T' in row['dateBill']:
                            row['dateBill'] = row['dateBill'].split('T')[0]
                            
                        else:
                            logger.debug("No se requiere corrección para dateBill")

                    if 'datePayment' in row:
                        date_payment = row['datePayment']
                       

                        # Verificar si datePayment es None y asignar un valor predeterminado
                        if date_payment is None:
                            row['datePayment'] = "SIN_FECHA"
                            
                        elif 'T' in date_payment:
                            row['datePayment'] = date_payment.split('T')[0]
                            
                        else:
                            logger.debug("No se requiere corrección para datePayment")
                    else:
                        logger.debug("datePayment no está presente en los datos de la factura.")

                    if 'expirationDate' in row:
                        expiration_date = row['expirationDate']
                        

                        # Verificar si expirationDate es None y asignar un valor predeterminado
                        if expiration_date is None:
                            row['expirationDate'] = "SIN_FECHA"
                            
                        elif 'T' in expiration_date:
                            row['expirationDate'] = expiration_date.split('T')[0]
                            
                        else:
                            logger.debug("No se requiere corrección para expirationDate")
                    else:
                        logger.debug("expirationDate no está presente en los datos de la factura.")

                    # Serialización
                    
                    serializer = BillSerializer(data=row, context={'request': request})

                    # Verificar si la serialización es válida
                    if serializer.is_valid():
                        
                        try:
                            # Intento de guardado en base de datos
                            saved_bill = serializer.save()

                        except Exception as save_error:
                            logger.error(f"Error al guardar la factura: {save_error}")
                            return response(
                                {'error': True, 'message': f"Error al guardar la factura: {str(save_error)}"}, 500)
                    else:
                        logger.error(f"Errores de validación en la factura: {serializer.errors}")
                        return response({'error': True, 'message': serializer.errors}, 400)

                logger.info("Todas las facturas se han procesado y guardado correctamente")

                return response({'error': False, 'message': 'Facturas creadas', 'failedBills': failedBills}, 201)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['admin','third'])
    def get(self, request, pk=None):
        try:
            # Normalizamos los parámetros (convertimos "" a None)
            params = {
                k: v if v != "" else None 
                for k, v in request.query_params.items()
            }
            
            # Verificamos si hay parámetros con valores reales
            has_valid_params = any(v is not None for v in params.values())
            
            if has_valid_params:
                logger.debug(f"Query params recibidos: {params}")
                
                # --- CASO 1: Búsqueda inteligente SIN filtros adicionales ---
                if (params.get('emitter_or_payer_or_billId') is not None and 
                    params.get('mode') == 'intelligent_query' and 
                    params.get('operation') is None and 
                    params.get('startDate') is None and 
                    params.get('endDate') is None and
                    params.get('typeBill') is None and
                    params.get('channel') is None):
                    
                    logger.debug('Caso 1: Búsqueda inteligente sola')
                    search_term = params.get('emitter_or_payer_or_billId')
                    bills = Bill.objects.filter(
                        Q(emitterName__icontains=search_term) |
                        Q(payerName__icontains=search_term) |
                        Q(billId__icontains=search_term),
                        state=1
                    )

                # --- CASO 2: Solo filtro por typeBill ---
                elif (params.get('emitter_or_payer_or_billId') is None and 
                       params.get('mode') == 'intelligent_query' and 
                 
                    params.get('operation') is None and 
                    params.get('startDate') is None and 
                    params.get('endDate') is None and 
                    params.get('typeBill') is not None and
                    params.get('channel') is None):
                    
                    logger.debug('Caso 2: Solo typeBill')
                    bills = Bill.objects.filter(
                        typeBill=params.get('typeBill'),
                        state=1
                    )

                # --- CASO 3: Búsqueda inteligente + typeBill ---
                elif (params.get('emitter_or_payer_or_billId') is not None and 
                    params.get('mode') == 'intelligent_query' and 
                    params.get('operation') is None and 
                    params.get('startDate') is None and 
                    params.get('endDate') is None and 
                    params.get('typeBill') is not None and
                    params.get('channel') is None):
                    
                    logger.debug('Caso 3: Búsqueda + typeBill')
                    search_term = params.get('emitter_or_payer_or_billId')
                    bills = Bill.objects.filter(
                        Q(emitterName__icontains=search_term) |
                        Q(payerName__icontains=search_term) |
                        Q(billId__icontains=search_term),
                        typeBill=params.get('typeBill'),
                        state=1
                    )

                # --- CASO 4: Búsqueda inteligente + fechas ---
                elif (params.get('emitter_or_payer_or_billId') is not None and 
                    params.get('mode') == 'intelligent_query' and 
                    params.get('operation') is None and 
                    params.get('startDate') is not None and 
                    params.get('endDate') is not None and 
                    params.get('typeBill') is None and
                    params.get('channel') is None):
                    
                    logger.debug('Caso 4: Búsqueda + fechas')
                    search_term = params.get('emitter_or_payer_or_billId')
                    bills = Bill.objects.filter(
                        Q(emitterName__icontains=search_term) |
                        Q(payerName__icontains=search_term) |
                        Q(billId__icontains=search_term),
                        dateBill__gte=params.get('startDate'),
                        dateBill__lte=params.get('endDate'),
                        state=1
                    )

                # --- CASO 5: Búsqueda + fechas + typeBill ---
                elif (params.get('emitter_or_payer_or_billId') is not None and 
                    params.get('mode') == 'intelligent_query' and 
                    params.get('operation') is None and 
                    params.get('startDate') is not None and 
                    params.get('endDate') is not None and 
                    params.get('typeBill') is not None and
                    params.get('channel') is None):
                    
                    logger.debug('Caso 5: Búsqueda + fechas + typeBill')
                    search_term = params.get('emitter_or_payer_or_billId')
                    bills = Bill.objects.filter(
                        Q(emitterName__icontains=search_term) |
                        Q(payerName__icontains=search_term) |
                        Q(billId__icontains=search_term),
                        typeBill=params.get('typeBill'),
                        dateBill__gte=params.get('startDate'),
                        dateBill__lte=params.get('endDate'),
                        state=1
                    )

                # --- CASO 6: Solo filtro por channel (autogestión) ---
                elif (params.get('emitter_or_payer_or_billId') is None and 
                    params.get('mode') == 'intelligent_query' and 
                    params.get('operation') is None and 
                    params.get('startDate') is None and 
                    params.get('endDate') is None and 
                    params.get('typeBill') is None and
                    params.get('channel') == 'autogestion'):
                    
                    logger.debug('Caso 6: Solo channel=autogestion')
                    bills = Bill.objects.filter(
                        integrationCode__isnull=False,
                        integrationCode__gt='',  # Mayor que cadena vacía
                        state=1
                    )

                # --- CASO 7: Solo filtro por channel (no-autogestion) ---
                elif (params.get('emitter_or_payer_or_billId') is None and 
                      params.get('mode') == 'intelligent_query' and 
                    params.get('operation') is None and 
                    params.get('startDate') is None and 
                    params.get('endDate') is None and 
                    params.get('typeBill') is None and
                    params.get('channel') == 'no-autogestion'):
                    
                    logger.debug('Caso 7: Solo channel=no-autogestion')
                    bills = Bill.objects.filter(
                        (Q(integrationCode__isnull=True) | Q(integrationCode__exact='')) & Q(state=1)
                    )

                # --- CASO 8: Búsqueda + channel ---
                elif (params.get('emitter_or_payer_or_billId') is not None and 
                    params.get('mode') == 'intelligent_query' and 
                    params.get('operation') is None and 
                    params.get('startDate') is None and 
                    params.get('endDate') is None and 
                    params.get('typeBill') is None and
                    params.get('channel') is not None):
                    
                    logger.debug('Caso 8: Búsqueda + channel')
                    search_term = params.get('emitter_or_payer_or_billId')
                    channel_filter = Q(integrationCode__isnull=False, integrationCode__gt='') if params.get('channel') == 'autogestion' else Q(Q(integrationCode__isnull=True) | Q(integrationCode__exact=''))
                    
                    bills = Bill.objects.filter(
                        (Q(emitterName__icontains=search_term) |
                        Q(payerName__icontains=search_term) |
                        Q(billId__icontains=search_term)),
                        channel_filter,
                        state=1
                    )

                # --- CASO 9: Búsqueda + fechas + channel ---
                elif (params.get('emitter_or_payer_or_billId') is not None and 
                    params.get('mode') == 'intelligent_query' and 
                    params.get('operation') is None and 
                    params.get('startDate') is not None and 
                    params.get('endDate') is not None and 
                    params.get('typeBill') is None and
                    params.get('channel') is not None):
                    
                    logger.debug('Caso 9: Búsqueda + fechas + channel')
                    search_term = params.get('emitter_or_payer_or_billId')
                    channel_filter = Q(integrationCode__isnull=False, integrationCode__gt='') if params.get('channel') == 'autogestion' else Q(Q(integrationCode__isnull=True) | Q(integrationCode__exact=''))
                    
                    bills = Bill.objects.filter(
                        (Q(emitterName__icontains=search_term) |
                        Q(payerName__icontains=search_term) |
                        Q(billId__icontains=search_term)),
                        channel_filter,
                        dateBill__gte=params.get('startDate'),
                        dateBill__lte=params.get('endDate'),
                        state=1
                    )

                # --- CASO 10: TODOS LOS FILTROS (búsqueda + fechas + typeBill + channel) ---
                elif (params.get('emitter_or_payer_or_billId') is not None and 
                    params.get('mode') == 'intelligent_query' and 
                    params.get('operation') is None and 
                    params.get('startDate') is not None and 
                    params.get('endDate') is not None and 
                    params.get('typeBill') is not None and
                    params.get('channel') is not None):
                    
                    logger.debug('Caso 10: TODOS LOS FILTROS')
                    search_term = params.get('emitter_or_payer_or_billId')
                    
                    # Construimos el Q object para channel
                    if params.get('channel') == 'autogestion':
                        channel_q = Q(integrationCode__isnull=False) & ~Q(integrationCode__exact='')
                    else:
                        channel_q = Q(integrationCode__isnull=True) | Q(integrationCode__exact='')
                    
                    # Filtro combinado (todos los Q objects juntos)
                    bills = Bill.objects.filter(
                        Q(emitterName__icontains=search_term) |
                        Q(payerName__icontains=search_term) |
                        Q(billId__icontains=search_term),
                        Q(typeBill=params.get('typeBill')),
                        channel_q,
                        Q(dateBill__gte=params.get('startDate')),
                        Q(dateBill__lte=params.get('endDate')),
                        Q(state=1)
                    )
                elif (params.get('emitter_or_payer_or_billId') and 
                    params.get('mode') == 'intelligent_query' and 
                    params.get('typeBill') and 
                    params.get('channel') == 'autogestion' and 
                    not params.get('startDate')):
                    bills = Bill.objects.filter(
                        # Búsqueda inteligente
                        typeBill=params.get('typeBill'),
                        integrationCode__isnull=False,
                        integrationCode__gt='',
                        state=1
                    )

                elif (params.get('emitter_or_payer_or_billId') and 
                    params.get('mode') == 'intelligent_query' and 
                    params.get('typeBill') and 
                    params.get('channel') == 'no-autogestion' and 
                    not params.get('startDate')):
                    bills = Bill.objects.filter(
                        # Búsqueda inteligente
                        typeBill=params.get('typeBill'),
                        integrationCode__isnull=True,
                
                        state=1
                    )

                
                # --- CASOS ESPECIALES (operation, opId, etc.) ---
                # Búsqueda por opId

                elif (not params.get('emitter_or_payer_or_billId') and 
                    params.get('mode') == 'intelligent_query' and 
                    params.get('typeBill') and 
                    params.get('channel') == 'autogestion' and 
                    params.get('startDate')):
                    bills = Bill.objects.filter(
                        typeBill=params.get('typeBill'),
                        integrationCode__isnull=False,
                        integrationCode__gt='',
                        dateBill__gte=params.get('startDate'),
                        dateBill__lte=params.get('endDate'),
                        state=1
                    )
                elif params.get('opId') is not None:
                    logger.debug('Caso opId')
                    try:
                        opId = params.get('opId')
                        logger.debug(f'{opId}')
                        bill_list = []
                        operations = PreOperation.objects.filter(opId=opId)
                        
                        for op in operations:
                            bill = op.bill
                            bill_list.append({
                                'id': bill.id,
                                'billId': bill.billId,
                                'total': bill.total,
                                'opAmount': op.payedAmount,
                                'opExpiration': op.opExpiration,
                                'dateBill': op.opDate
                            })
                        return response({'error': False, 'data': bill_list}, 200)
                    except Exception as e:
                        logger.error(f"Error buscando por opId: {str(e)}")
                        return response({'error': True, 'message': str(e)}, 400)
                elif (not params.get('emitter_or_payer_or_billId') and 
                    params.get('mode') == 'intelligent_query' and 
                    params.get('typeBill') and 
                    params.get('channel') == 'autogestion' and 
                    not params.get('startDate') and 
                    not params.get('endDate')):
                    logger.debug('Caso 12: typeBill + autogestion')
                    bills = Bill.objects.filter(
                        typeBill=params.get('typeBill'),
                        integrationCode__isnull=False,
                        integrationCode__gt='',
                        state=1
                    )

                elif (not params.get('emitter_or_payer_or_billId') and 
                    params.get('mode') == 'intelligent_query' and 
                    params.get('typeBill') and 
                    params.get('channel') == 'no-autogestion' and 
                    not params.get('startDate') and 
                    not params.get('endDate')):
                    logger.debug('Caso 13: typeBill + no-autogestion')
                    bills = Bill.objects.filter(
                        (Q(typeBill=params.get('typeBill')) &
                        (Q(integrationCode__isnull=True) | Q(integrationCode__exact='')) &
                        Q(state=1))
                    )

                elif (not params.get('emitter_or_payer_or_billId') and 
                    params.get('mode') == 'intelligent_query' and 
                    not params.get('typeBill') and 
                    params.get('channel') == 'autogestion' and 
                    params.get('startDate') and 
                    params.get('endDate')):
                    logger.debug('Caso 15: autogestion + fechas')
                    bills = Bill.objects.filter(
                        integrationCode__isnull=False,
                        integrationCode__gt='',
                        dateBill__gte=params.get('startDate'),
                        dateBill__lte=params.get('endDate'),
                        state=1
                    )

                elif (not params.get('emitter_or_payer_or_billId') and 
                    params.get('mode') == 'intelligent_query' and 
                    not params.get('typeBill') and 
                    params.get('channel') == 'no-autogestion' and 
                    params.get('startDate') and 
                    params.get('endDate')):
                    logger.debug('Caso 16: no-autogestion + fechas')
                    bills = Bill.objects.filter(
                        (Q(integrationCode__isnull=True) | Q(integrationCode__exact='')) &
                        Q(dateBill__gte=params.get('startDate')) &
                        Q(dateBill__lte=params.get('endDate')) &
                        Q(state=1)
                    )

                elif (params.get('emitter_or_payer_or_billId') and 
                    params.get('mode') == 'intelligent_query' and 
                    params.get('typeBill') and 
                    params.get('channel') == 'autogestion' and 
                    not params.get('startDate') and 
                    not params.get('endDate')):
                    
                    logger.debug('Caso 10: Búsqueda + typeBill + autogestion')
                    search_term = params.get('emitter_or_payer_or_billId')
                    bills = Bill.objects.filter(
                        Q(emitterName__icontains=search_term) |
                        Q(payerName__icontains=search_term) |
                        Q(billId__icontains=search_term),
                        typeBill=params.get('typeBill'),
                        integrationCode__isnull=False,
                        integrationCode__gt='',
                        state=1
                    )

                elif (params.get('emitter_or_payer_or_billId') and 
                    params.get('mode') == 'intelligent_query' and 
                    params.get('typeBill') and 
                    not params.get('channel') and 
                    params.get('startDate') and 
                    params.get('endDate')):
                    
                    logger.debug('Caso 12: Búsqueda + typeBill + fechas')
                    search_term = params.get('emitter_or_payer_or_billId')
                    bills = Bill.objects.filter(
                        Q(emitterName__icontains=search_term) |
                        Q(payerName__icontains=search_term) |
                        Q(billId__icontains=search_term),
                        typeBill=params.get('typeBill'),
                        dateBill__gte=params.get('startDate'),
                        dateBill__lte=params.get('endDate'),
                        state=1
                    )


                elif (params.get('emitter_or_payer_or_billId') and 
                    params.get('mode') == 'intelligent_query' and 
                    not params.get('typeBill') and 
                    params.get('channel') == 'autogestion' and 
                    params.get('startDate') and 
                    params.get('endDate')):
                    
                    logger.debug('Caso 13: Búsqueda + autogestion + fechas')
                    search_term = params.get('emitter_or_payer_or_billId')
                    bills = Bill.objects.filter(
                        Q(emitterName__icontains=search_term) |
                        Q(payerName__icontains=search_term) |
                        Q(billId__icontains=search_term),
                        integrationCode__isnull=False,
                        integrationCode__gt='',
                        dateBill__gte=params.get('startDate'),
                        dateBill__lte=params.get('endDate'),
                        state=1
                    )
                elif (params.get('emitter_or_payer_or_billId') and 
                    params.get('mode') == 'intelligent_query' and 
                    not params.get('typeBill') and 
                    params.get('channel') == 'no-autogestion' and 
                    params.get('startDate') and 
                    params.get('endDate')):
                    
                    logger.debug('Caso 14: Búsqueda + no-autogestion + fechas')
                    search_term = params.get('emitter_or_payer_or_billId')
                    bills = Bill.objects.filter(
                        Q(emitterName__icontains=search_term) |
                        Q(payerName__icontains=search_term) |
                        Q(billId__icontains=search_term),
                        Q(integrationCode__isnull=True) | Q(integrationCode__exact=''),
                        dateBill__gte=params.get('startDate'),
                        dateBill__lte=params.get('endDate'),
                        state=1
                    )
                elif (not params.get('emitter_or_payer_or_billId') and 
                    params.get('mode') == 'intelligent_query' and 
                    params.get('typeBill') and 
                    params.get('channel') == 'autogestion' and 
                    not params.get('startDate') and 
                    not params.get('endDate')):
                    
                    logger.debug('Caso 15: typeBill + autogestion')
                    bills = Bill.objects.filter(
                        typeBill=params.get('typeBill'),
                        integrationCode__isnull=False,
                        integrationCode__gt='',
                        state=1
                    )
                elif (not params.get('emitter_or_payer_or_billId') and 
                    params.get('mode') == 'intelligent_query' and 
                    params.get('typeBill') and 
                    params.get('channel') == 'no-autogestion' and 
                    not params.get('startDate') and 
                    not params.get('endDate')):
                    
                    logger.debug('Caso 16: typeBill + no-autogestion')
                    bills = Bill.objects.filter(
                        # Primero los objetos Q
                        Q(integrationCode__isnull=True) | Q(integrationCode__exact=''),
                        
                        # Luego los argumentos de palabra clave
                        typeBill=params.get('typeBill'),
                        state=1
                    )
                elif (not params.get('emitter_or_payer_or_billId') and 
                    params.get('mode') == 'intelligent_query' and 
                    params.get('typeBill') and 
                    not params.get('channel') and 
                    params.get('startDate') and 
                    params.get('endDate')):
                    
                    logger.debug('Caso 17: typeBill + fechas')
                    bills = Bill.objects.filter(
                        typeBill=params.get('typeBill'),
                        dateBill__gte=params.get('startDate'),
                        dateBill__lte=params.get('endDate'),
                        state=1
                    )
                elif (not params.get('emitter_or_payer_or_billId') and 
                    params.get('mode') == 'intelligent_query' and 
                    not params.get('typeBill') and 
                    params.get('channel') == 'autogestion' and 
                    params.get('startDate') and 
                    params.get('endDate')):
                    
                    logger.debug('Caso 18: autogestion + fechas')
                    bills = Bill.objects.filter(
                        integrationCode__isnull=False,
                        integrationCode__gt='',
                        dateBill__gte=params.get('startDate'),
                        dateBill__lte=params.get('endDate'),
                        state=1
                    )
                elif (not params.get('emitter_or_payer_or_billId') and 
                    params.get('mode') == 'intelligent_query' and 
                    not params.get('typeBill') and 
                    params.get('channel') == 'no-autogestion' and 
                    params.get('startDate') and 
                    params.get('endDate')):
                    
                    logger.debug('Caso 19: no-autogestion + fechas')
                    bills = Bill.objects.filter(
                        Q(integrationCode__isnull=True) | Q(integrationCode__exact=''),
                        dateBill__gte=params.get('startDate'),
                        dateBill__lte=params.get('endDate'),
                        state=1
                    )   
                elif (params.get('emitter_or_payer_or_billId') and 
                    params.get('mode') == 'intelligent_query' and 
                    params.get('typeBill') and 
                    params.get('channel') == 'no-autogestion' and 
                    not params.get('startDate') and 
                    not params.get('endDate')):
                    
                    logger.debug('Caso 11: Búsqueda + typeBill + no-autogestion')
                    search_term = params.get('emitter_or_payer_or_billId')
                    bills = Bill.objects.filter(
                        (Q(emitterName__icontains=search_term) |
                        Q(payerName__icontains=search_term) |
                        Q(billId__icontains=search_term)) &
                        Q(typeBill=params.get('typeBill')) &
                        (Q(integrationCode__isnull=True) | Q(integrationCode__exact='')) &
                        Q(state=1)
                    )

                elif (not params.get('emitter_or_payer_or_billId') and 
                    params.get('mode') == 'intelligent_query' and 
                    params.get('typeBill') and 
                    params.get('channel') == 'autogestion' and 
                    params.get('startDate') and 
                    params.get('endDate')):
                    
                    logger.debug('Caso 20: typeBill + autogestion + fechas')
                    bills = Bill.objects.filter(
                        typeBill=params.get('typeBill'),
                        integrationCode__isnull=False,
                        integrationCode__gt='',
                        dateBill__gte=params.get('startDate'),
                        dateBill__lte=params.get('endDate'),
                        state=1
                    )
                elif (not params.get('emitter_or_payer_or_billId') and 
                    params.get('mode') == 'intelligent_query' and 
                    params.get('typeBill') and 
                    params.get('channel') == 'no-autogestion' and 
                    params.get('startDate') and 
                    params.get('endDate')):
                    
                    logger.debug('Caso 21: typeBill + no-autogestion + fechas')
                    bills = Bill.objects.filter(
                        (Q(integrationCode__isnull=True) | Q(integrationCode__exact='')),
                        Q(typeBill=params.get('typeBill')),
                        Q(dateBill__gte=params.get('startDate')),
                        Q(dateBill__lte=params.get('endDate')),
                        Q(state=1)
                    )
                elif (params.get('emitter_or_payer_or_billId') and 
                    params.get('mode') == 'intelligent_query' and 
                    params.get('typeBill') and 
                    params.get('channel') == 'autogestion' and 
                    params.get('startDate') and 
                    params.get('endDate')):
                    
                    logger.debug('Caso 22: Búsqueda + typeBill + autogestion + fechas')
                    search_term = params.get('emitter_or_payer_or_billId')
                    bills = Bill.objects.filter(
                        Q(emitterName__icontains=search_term) |
                        Q(payerName__icontains=search_term) |
                        Q(billId__icontains=search_term),
                        typeBill=params.get('typeBill'),
                        integrationCode__isnull=False,
                        integrationCode__gt='',
                        dateBill__gte=params.get('startDate'),
                        dateBill__lte=params.get('endDate'),
                        state=1
                    )
                elif (params.get('emitter_or_payer_or_billId') and 
                    params.get('mode') == 'intelligent_query' and 
                    params.get('typeBill') and 
                    params.get('channel') == 'no-autogestion' and 
                    params.get('startDate') and 
                    params.get('endDate')):
                    
                    logger.debug('Caso 23: Búsqueda + typeBill + no-autogestion + fechas')
                    search_term = params.get('emitter_or_payer_or_billId')
                    bills = Bill.objects.filter(
                        # Todos los argumentos posicionales (Q objects) primero
                        Q(emitterName__icontains=search_term) |
                        Q(payerName__icontains=search_term) |
                        Q(billId__icontains=search_term),
                        (Q(integrationCode__isnull=True) | Q(integrationCode__exact='')),
                        typeBill=params.get('typeBill'),
                        dateBill__gte=params.get('startDate'),
                        dateBill__lte=params.get('endDate'),
                        state=1
                    )
                # Búsqueda por operation
                elif params.get('operation') is not None:
                    try:
                        bill_list = []
                        operations = PreOperation.objects.filter(opId=params.get('operation'))
                        for op in operations:
                            bill_list.append(op.bill)
                        
                        page = self.paginate_queryset(bill_list)
                        if page is not None:
                            serializer = BillReadOnlySerializer(page, many=True)
                            return self.get_paginated_response(serializer.data)
                    except Exception as e:
                        logger.error(f"Error buscando por operation: {str(e)}")
                        return response({'error': True, 'message': str(e)}, 400)
                elif (params.get('operation') and 
                    params.get('typeBill')):
                    
                    logger.debug('Caso 25: operation + typeBill')
                    try:
                        bill_list = []
                        operations = PreOperation.objects.filter(
                            opId=params.get('operation'),
                            bill__typeBill=params.get('typeBill')
                        )
                        for op in operations:
                            bill_list.append(op.bill)
                        
                        page = self.paginate_queryset(bill_list)
                        if page is not None:
                            serializer = BillReadOnlySerializer(page, many=True)
                            return self.get_paginated_response(serializer.data)
                    except Exception as e:
                        logger.error(f"Error buscando por operation + typeBill: {str(e)}")
                        return response({'error': True, 'message': str(e)}, 400)
                elif (params.get('operation') and 
                    params.get('channel') == 'autogestion'):
                    
                    logger.debug('Caso 26: operation + autogestion')
                    try:
                        bill_list = []
                        operations = PreOperation.objects.filter(
                            opId=params.get('operation'),
                            bill__integrationCode__isnull=False,
                            bill__integrationCode__gt=''
                        )
                        for op in operations:
                            bill_list.append(op.bill)
                        
                        page = self.paginate_queryset(bill_list)
                        if page is not None:
                            serializer = BillReadOnlySerializer(page, many=True)
                            return self.get_paginated_response(serializer.data)
                    except Exception as e:
                        logger.error(f"Error buscando por operation + autogestion: {str(e)}")
                        return response({'error': True, 'message': str(e)}, 400)
                    
                elif (params.get('operation') and 
                    params.get('channel') == 'autogestion'):
                    
                    logger.debug('Caso 26: operation + autogestion')
                    try:
                        bill_list = []
                        operations = PreOperation.objects.filter(
                            opId=params.get('operation'),
                            bill__integrationCode__isnull=False,
                            bill__integrationCode__gt=''
                        )
                        for op in operations:
                            bill_list.append(op.bill)
                        
                        page = self.paginate_queryset(bill_list)
                        if page is not None:
                            serializer = BillReadOnlySerializer(page, many=True)
                            return self.get_paginated_response(serializer.data)
                    except Exception as e:
                        logger.error(f"Error buscando por operation + autogestion: {str(e)}")
                        return response({'error': True, 'message': str(e)}, 400)
                    
                elif (params.get('operation') and 
                    params.get('channel') == 'no-autogestion'):
                    
                    logger.debug('Caso 27: operation + no-autogestion')
                    try:
                        bill_list = []
                        operations = PreOperation.objects.filter(
                            Q(opId=params.get('operation')) &
                            (Q(bill__integrationCode__isnull=True) | Q(bill__integrationCode__exact=''))
                        )
                        for op in operations:
                            bill_list.append(op.bill)
                        
                        page = self.paginate_queryset(bill_list)
                        if page is not None:
                            serializer = BillReadOnlySerializer(page, many=True)
                            return self.get_paginated_response(serializer.data)
                    except Exception as e:
                        logger.error(f"Error buscando por operation + no-autogestion: {str(e)}")
                        return response({'error': True, 'message': str(e)}, 400)
                    
                elif (params.get('operation') and 
                    params.get('startDate') and 
                    params.get('endDate')):
                    
                    logger.debug('Caso 28: operation + fechas')
                    try:
                        bill_list = []
                        operations = PreOperation.objects.filter(
                            opId=params.get('operation'),
                            opDate__gte=params.get('startDate'),
                            opDate__lte=params.get('endDate')
                        )
                        for op in operations:
                            bill_list.append(op.bill)
                        
                        page = self.paginate_queryset(bill_list)
                        if page is not None:
                            serializer = BillReadOnlySerializer(page, many=True)
                            return self.get_paginated_response(serializer.data)
                    except Exception as e:
                        logger.error(f"Error buscando por operation + fechas: {str(e)}")
                        return response({'error': True, 'message': str(e)}, 400)
                    

                elif (params.get('operation') and 
                    params.get('typeBill') and 
                    params.get('channel') == 'autogestion'):
                    
                    logger.debug('Caso 29: operation + typeBill + autogestion')
                    try:
                        bill_list = []
                        operations = PreOperation.objects.filter(
                            opId=params.get('operation'),
                            bill__typeBill=params.get('typeBill'),
                            bill__integrationCode__isnull=False,
                            bill__integrationCode__gt=''
                        )
                        for op in operations:
                            bill_list.append(op.bill)
                        
                        page = self.paginate_queryset(bill_list)
                        if page is not None:
                            serializer = BillReadOnlySerializer(page, many=True)
                            return self.get_paginated_response(serializer.data)
                    except Exception as e:
                        logger.error(f"Error buscando por operation + typeBill + autogestion: {str(e)}")
                        return response({'error': True, 'message': str(e)}, 400)
                    

                elif (params.get('operation') and 
                    params.get('typeBill') and 
                    params.get('startDate') and 
                    params.get('endDate')):
                    
                    logger.debug('Caso 30: operation + typeBill + fechas')
                    try:
                        bill_list = []
                        operations = PreOperation.objects.filter(
                            opId=params.get('operation'),
                            bill__typeBill=params.get('typeBill'),
                            opDate__gte=params.get('startDate'),
                            opDate__lte=params.get('endDate')
                        )
                        for op in operations:
                            bill_list.append(op.bill)
                        
                        page = self.paginate_queryset(bill_list)
                        if page is not None:
                            serializer = BillReadOnlySerializer(page, many=True)
                            return self.get_paginated_response(serializer.data)
                    except Exception as e:
                        logger.error(f"Error buscando por operation + typeBill + fechas: {str(e)}")
                        return response({'error': True, 'message': str(e)}, 400)
                    
                elif (params.get('operation') and 
                    params.get('channel') == 'autogestion' and 
                    params.get('startDate') and 
                    params.get('endDate')):
                    
                    logger.debug('Caso 31: operation + autogestion + fechas')
                    try:
                        bill_list = []
                        operations = PreOperation.objects.filter(
                            opId=params.get('operation'),
                            bill__integrationCode__isnull=False,
                            bill__integrationCode__gt='',
                            opDate__gte=params.get('startDate'),
                            opDate__lte=params.get('endDate')
                        )
                        for op in operations:
                            bill_list.append(op.bill)
                        
                        page = self.paginate_queryset(bill_list)
                        if page is not None:
                            serializer = BillReadOnlySerializer(page, many=True)
                            return self.get_paginated_response(serializer.data)
                    except Exception as e:
                        logger.error(f"Error buscando por operation + autogestion + fechas: {str(e)}")
                        return response({'error': True, 'message': str(e)}, 400)
                    
                elif (params.get('operation') and 
                    params.get('typeBill') and 
                    params.get('channel') == 'autogestion' and 
                    params.get('startDate') and 
                    params.get('endDate')):
                    
                    logger.debug('Caso 32: operation + typeBill + autogestion + fechas')
                    try:
                        bill_list = []
                        operations = PreOperation.objects.filter(
                            opId=params.get('operation'),
                            bill__typeBill=params.get('typeBill'),
                            bill__integrationCode__isnull=False,
                            bill__integrationCode__gt='',
                            opDate__gte=params.get('startDate'),
                            opDate__lte=params.get('endDate')
                        )
                        for op in operations:
                            bill_list.append(op.bill)
                        
                        page = self.paginate_queryset(bill_list)
                        if page is not None:
                            serializer = BillReadOnlySerializer(page, many=True)
                            return self.get_paginated_response(serializer.data)
                    except Exception as e:
                        logger.error(f"Error buscando por operation + typeBill + autogestion + fechas: {str(e)}")
                        return response({'error': True, 'message': str(e)}, 400)
                # Búsqueda por payerId
                elif params.get('payerId') is not None:
                    try:
                        bill = Bill.objects.get(id=params.get('payerId'))
                        client = Client.objects.get(document_number=bill.payerId)
                        return response({'error': False, 'data': client.id}, 200)
                    except Bill.DoesNotExist:
                        return response({'error': True, 'message': 'Factura no encontrada'}, 404)
                    except Client.DoesNotExist:
                        return response({'error': True, 'message': 'Pagador no Registrado'}, 404)
                    except Exception as e:
                        logger.error(f"Error buscando por payerId: {str(e)}")
                        return response({'error': True, 'message': str(e)}, 400)
                
                # Búsqueda por reBuy
                elif params.get('reBuy') is not None:
                    try:
                        bill = PreOperation.objects.filter(
                            bill_id=params.get('reBuy')
                        ).order_by('-opId').first()
                        if bill:
                            serializer = PreOperationReadOnlySerializer(bill)
                            return response({'error': False, 'data': serializer.data}, 200)
                        return response({'error': True, 'message': 'No se encontraron operaciones'}, 404)
                    except Exception as e:
                        logger.error(f"Error buscando por reBuy: {str(e)}")
                        return response({'error': True, 'message': str(e)}, 400)
                
                # Búsqueda por billEvent
                elif params.get('billEvent') is not None:
                    try:
                        bill = Bill.objects.get(id=params.get('billEvent'))
                        if bill.cufe:
                            serializer = BillEventReadOnlySerializer(bill)
                            return response({'error': False, 'data': serializer.data}, 200)
                        serializer = BillReadOnlySerializer(bill)
                        return response({'error': False, 'data': serializer.data}, 200)
                    except Bill.DoesNotExist:
                        return response({'error': True, 'message': 'Factura no encontrada'}, 404)
                    except Exception as e:
                        logger.error(f"Error buscando por billEvent: {str(e)}")
                        return response({'error': True, 'message': str(e)}, 400)
                
                # Si hay parámetros pero no coinciden con ningún caso
                else:
                    bills = Bill.objects.filter(state=1)
                
                # Paginación común para los casos que devuelven querysets
                page = self.paginate_queryset(bills)
                if page is not None:
                    serializer = BillReadOnlySerializer(page, many=True)
                    return self.get_paginated_response(serializer.data)
            
            # Caso cuando no hay parámetros válidos o todos están vacíos
            bills = Bill.objects.filter(state=1)
            
            # Búsqueda por pk (ID de cliente o factura)
            if pk:
                logger.debug('j')
                try:
                    # Intenta obtener un cliente con este pk
                    client = Client.objects.get(pk=pk)
                    # Si existe el cliente, busca sus facturas
                    bill = Bill.objects.filter(
                        Q(emitterId=pk) | Q(emitterId=client.document_number)
                    )
                    serializer = BillReadOnlySerializer(bill, many=True)
                    return response({'error': False, 'data': serializer.data}, 200)
                except Client.DoesNotExist:
                    # Si no es un cliente, tratar como búsqueda general
                    pass
                except Exception as e:
                    return response({'error': True, 'message': str(e)}, 400)
            
            page = self.paginate_queryset(bills)
            if page is not None:
                serializer = BillReadOnlySerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
        
        except Exception as e:
            logger.error(f"Error en endpoint /api/bill/: {str(e)}", exc_info=True)
            return response({
                'error': True,
                'message': 'Error interno del servidor',
                'detail': str(e)
            }, 500)

    @checkRole(['admin'])
    def patch(self, request, pk):
        try:
            bill = Bill.objects.get(pk=pk)
            serializer = BillSerializer(bill, data=request.data, context={
                                        'request': request}, partial=True)
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'message': 'Factura actualizada', 'data': serializer.data}, 200)
            else:
                return response({'error': True, 'data': serializer.errors}, 400)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['admin'])
    def delete(self, request, pk):
        try:
            # verify if the bill is in an operation
            op = PreOperation.objects.filter(bill=pk)
            if len(op) > 0:
                return response({'error': True, 'message': 'La factura no se puede eliminar porque esta en una operacion'}, 400)
            else:
                bill = Bill.objects.get(pk=pk)
                bill.delete()
            return response({'error': False, 'message': 'Factura eliminada'}, 200)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)


class readBillAV(BaseAV):
    @checkRole(['admin','third'])
    def post(self, request):
        parsedBills = []
        duplicatedBills = []
        failedBills = []
        try:
            for file in request.data['bills']:                      
                # decode base 64 file
                # if file has data:text/xml;base64, remove it
                if file.startswith('data:text/xml;base64,'):
                    logger.debug(f"if 1 read bill")
                    file = file.replace('data:text/xml;base64,', '')
                fileName = f'{gen_uuid()}.xml'
                logger.debug(f" b64decode a realizar")
                logger.debug(f" fileName : {fileName}")
                logger.debug(f" file : {file}")
                
                encoding_options = ['utf-8', 'utf-16', 'utf-32', 'utf-32-le']

                # Intentar decodificar en cada formato hasta que uno funcione
                xmlData = None  # Inicializar la variable donde almacenaremos el resultado
                for f in encoding_options:
                    try:
                        # Intentamos decodificar con la opción actual
                        xmlData = b64decode(file, validate=True).decode(f)
                        logger.debug(f"Formato válido encontrado: {f}")
                        break  # Salir del bucle si decodificación tiene éxito
                    except Exception as e:
                        logger.debug(f"No es formato {f}")
                        logger.debug({'error': True, 'message': str(e)})

                if xmlData is None:
                    logger.error("No se pudo decodificar el archivo con ningún formato.")
                    raise ValueError("El archivo no se pudo decodificar correctamente.")

                # Procesar el XML decodificado

                             
               # try:
                 #   xmlData = b64decode(file, validate=True).decode('utf-8')#aqui está el error
                   # logger.debug(f" b64decode UTF-8 realizado")
               # except:
                   # try:
                       # xml_bytes = b64decode(file, validate=True)
                       # # Detectar codificación
                       

                        # Decodificar usando la codificación detectada
                        
                       # xmlData = xml_bytes.decode('utf-16')
                       # logger.debug(f" b64decode UTF-16 realizado")
                    #except UnicodeDecodeError:
                      #  xmlData = xml_bytes.decode('utf-32')
                       # logger.debug(f" b64decode UTF-32 realizado")    
                    
                logger.debug(f" b64decode POR FIN realizado")
                with open(fileName, 'w') as f:
                    f.write(xmlData)
                logger.debug(f" parseXml lo va  realizar,{fileName}")
                parseXml = parseBill(fileName)
                logger.debug(f" parseBill realizado")
                parseXml['file'] = file
                logger.debug(f" parsedXml")
                # add the data:text/xml;base64, to the file
                parseXml['file'] = f'data:text/xml;base64,{file}'
                logger.debug(f" remove")
                os.remove(fileName)
                logger.debug(f"removed")

                
                logger.debug(f"logging.log")
                # check if the bill has cufe
                try:
                    logger.debug('entro al try')
                    #se lavida si el archivo que se lee posee errores
                    
                    logger.debug(f"{parseXml['cufe']}")
                    if  parseXml['cufe'] == "" or parseXml == None:
                        logger.debug(f" if cufe")
                        failedBills.append(parseXml)
                    else:
                        logger.debug(f"else cufe")
                        # validate if the bill is duplicated
                        bill = Bill.objects.filter(cufe=parseXml['cufe'])
                        logger.debug(f" filter cufe")
                        if len(bill) > 0:
                            logger.debug(f" if len bill")
                            
                            duplicatedBills.append(parseXml)
                            logger.debug(f" if len bill")
                        else:
                            logger.debug(f" else len")
                            parsedBills.append(parseXml)
                            
                        if len(failedBills):
                            return response({'error': True, 'message': "hay problemas con una factura por favor intentelo nuevamente"}, 500)
                except Exception as e:
                    return response({'error': True, 'message': str(e)}, 500)
                
            return response({'error': False, 'bills': parsedBills, 'duplicatedBills': duplicatedBills, 'failedBills':failedBills}, 200)    
        except Exception as e:
            logger.debug(f"error")
            return response({'error': True, 'message': str(e)}, 500)


class readCreditNoteAV(BaseAV):
    @checkRole(['admin','third'])
    def post(self, request):
        parsedCreditNotes = []
        for file in request.FILES.getlist('creditNotes'):
            parsedCreditNotes.append(parseCreditNote(file))
        return response({'error': False, 'data': parsedCreditNotes}, 200)

