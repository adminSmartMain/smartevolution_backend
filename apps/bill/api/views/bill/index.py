from django.db.models import Q
# Serializers
from apps.bill.api.serializers.index import BillSerializer, BillReadOnlySerializer, BillEventReadOnlySerializer,BillCreationSerializer,BillDetailSerializer
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
import requests
import uuid
from apps.bill.utils.billEvents import billEvents
from apps.bill.utils.updateBillEvents import updateBillEvents
import logging
from rest_framework.response import Response
from rest_framework import status
import requests
import environ
import os
from apps.bill.utils.updateMassiveTypeBill import updateMassiveTypeBill


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
import environ


class BillCreationManualAV(BaseAV):
    @checkRole(['admin','third'])
    def post(self, request):
        try:
      
            
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
                            pass

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
                
                
                # --- CASO 1: Búsqueda inteligente SIN filtros adicionales ---
                if (params.get('emitter_or_payer_or_billId') is not None and 
                    params.get('mode') == 'intelligent_query' and 
                    params.get('operation') is None and 
                    params.get('startDate') is None and 
                    params.get('endDate') is None and
                    params.get('typeBill') is None and
                    params.get('channel') is None):
                    
                    
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
                    
                   
                    bills = Bill.objects.filter(
                        typeBill=params.get('typeBill'),
                        state=1
                    )
                 # --- CASO : Solo filtro por fecha ---
                elif (params.get('emitter_or_payer_or_billId') is None and 
                       params.get('mode') == 'intelligent_query' and 
                 
                    params.get('operation') is None and 
                    params.get('startDate') is not None and 
                    params.get('endDate')  is not None  and 
                    params.get('typeBill') is None and
                    params.get('channel') is None):
                    
                    
                    bills = Bill.objects.filter(
                         dateBill__gte=params.get('startDate'),
                        dateBill__lte=params.get('endDate'),
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
                   
                    try:
                        opId = params.get('opId')
                        
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
                            logger.debug(bill.cufe)
                            
                            serializer = BillEventReadOnlySerializer(bill)
                            return response({'error': False, 'data': serializer.data}, 200)
                        else:
                            
                            serializer =BillDetailSerializer(bill)
                        return response({'error': False, 'data': serializer.data}, 200)
                    except Bill.DoesNotExist:
                        return response({'error': True, 'message': 'Factura no encontrada'}, 404)
                    except Exception as e:
                        logger.error(f"Error buscando por billEvent: {str(e)}")
                        return response({'error': True, 'message': str(e)}, 400)
                elif params.get('bill_operation') is not None:
                    
                    
                    bill_id = params.get('bill_operation')
                    emitter_id = params.get('emitter')  # Nuevo parámetro opcional
                    logger.debug(f'archivo index.py - bill_operation: {bill_id}, emitter: {emitter_id}')
                    try:
                        if emitter_id:
                            # Si se proporciona emitter_id, buscar por billId Y emitterId
                            try:
                                # Obtener el document_number del emisor
                                emitter_client = Client.objects.get(pk=emitter_id)
                                emitter_doc_number = emitter_client.document_number
                                logger.debug(f'Emisor document_number: {emitter_doc_number}')
                                # Buscar factura por billId y emitterId
                                bill = Bill.objects.get(
                                    billId=bill_id,
                                    emitterId=emitter_doc_number
                                )
                                logger.debug(f'archivo index.py - Factura encontrada: {bill.id}')
                            except Client.DoesNotExist:
                                return response({
                                    'error': True, 
                                    'message': f'Emisor con ID {emitter_id} no encontrado'
                                }, 404)
                        else:
                            # Si no se proporciona emitter_id, buscar solo por billId
                            bills = Bill.objects.filter(billId=bill_id)
                            
                            if bills.count() == 0:
                                return response({'error': True, 'message': 'Factura no encontrada'}, 404)
                            elif bills.count() > 1:
                                # Si hay múltiples facturas, devolver la primera con advertencia
                                bill = bills.first()
                                logger.warning(f'Múltiples facturas encontradas con billId {bill_id}. Usando la primera: {bill.id}')
                            else:
                                bill = bills.first()
                        
                        # Factura encontrada, proceder con la serialización
                        if bill.cufe:
                            
                            serializer =BillReadOnlySerializer(bill)
                            return response({'error': False, 'data': serializer.data}, 200)
                        
                        serializer = BillReadOnlySerializer(bill)
                        return response({'error': False, 'data': serializer.data}, 200)
                        
                    except Bill.DoesNotExist:
                        return response({'error': True, 'message': 'Factura no encontrada'}, 404)
                    except Exception as e:
                        logger.error(f"Error buscando por bill_operation: {str(e)}")
                        return response({'error': True, 'message': str(e)}, 400)
                # Si hay parámetros pero no coinciden con ningún caso
                else:
                    
                    bills = Bill.objects.filter(state=1)
                
                
                
                    page = self.paginate_queryset(bills)

                    if page is not None:

                        page_ids = [obj.id for obj in page]  # recuperar ids REALES

                        qs_page = Bill.objects.filter(id__in=page_ids)

                        updateMassiveTypeBill(qs_page, billEvents)

                        # refrescar los valores ya guardados
                        qs_page = list(Bill.objects.filter(id__in=page_ids))
                        logger.debug("REFRESCO")
                        logger.debug(qs_page)
                        # mantener orden original
                        ordered_page = sorted(qs_page, key=lambda x: page_ids.index(x.id))

                        serializer = BillReadOnlySerializer(ordered_page, many=True)
                        return self.get_paginated_response(serializer.data)

            
           # Caso cuando no hay parámetros válidos o todos están vacíos
            bills = Bill.objects.filter(state=1)

            # Búsqueda por pk (ID de cliente o factura)
            if pk:
                
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

            # 🔥🔥🔥 AQUI SE APLICA TU FUNCTION updateMassiveTypeBill 🔥🔥🔥
            if page is not None:
                logger.debug('sasaaaasdsfsdfsadfdffsd')
                updateMassiveTypeBill(page, billEvents)   # <<--- AQUI VA

                if params.get('billEvent') or request.method == 'GET' and 'billEvent' not in params:
                    # Usar serializador de lista para consultas generales
                    serializer = BillReadOnlySerializer(page, many=True)
                else:
                    # Usar serializador de detalle para casos específicos
                    serializer = BillDetailSerializer(page, many=True)

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
    @checkRole(['admin', 'third'])
    def post(self, request):
        parsedBills = []
        duplicatedLocalBills = []
        duplicatedBillyBills = []
        failedBills = []

        env = environ.Env()
        fideicomiso = request.data.get('fideicomiso', False)

        try:
            for file in request.data['bills']:

                # -------------------- DECODIFICAR XML --------------------
                if file.startswith('data:text/xml;base64,'):
                    file = file.replace('data:text/xml;base64,', '')

                fileName = f"{gen_uuid()}.xml"
                xmlData = None

                for codec in ['utf-8', 'utf-16', 'utf-32', 'utf-32-le']:
                    try:
                        xmlData = b64decode(file, validate=True).decode(codec)
                        break
                    except:
                        pass

                if xmlData is None:
                    failedBills.append({"message": "No se pudo decodificar XML"})
                    continue

                with open(fileName, 'w') as f:
                    f.write(xmlData)

                # -------------------- PARSEAR XML --------------------
                parsed = parseBill(fileName)
                os.remove(fileName)

                parsed['file'] = f"data:text/xml;base64,{file}"
                parsed['fideicomiso'] = fideicomiso

                # -------------------- VALIDAR CUFE --------------------
                if not parsed or parsed.get('cufe', '') == "":
                    failedBills.append({
                        "message": "Factura sin CUFE",
                        "file": parsed
                    })
                    continue

                # -------------------- VALIDAR DUPLICADO LOCAL --------------------
                if Bill.objects.filter(cufe=parsed['cufe']).exists():
                    duplicatedLocalBills.append({
                        "cufe": parsed['cufe'],
                        "message": "Factura ya existe en la base de datos"
                    })
                    continue

                # -------------------- SUBIR A BILLY --------------------
                token = env('PA_TOKEN') if fideicomiso else env('SMART_TOKEN')

                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }

                try:
                    r = requests.post(
                        "https://api.billy.com.co/v1/invoices/uploadByCufe",
                        headers=headers,
                        json={"cufe": parsed["cufe"]},
                        timeout=30
                    )

                    # ---------- SI LA FACTURA YA ESTÁ (409) → CONTINUAR ----------
                    if r.status_code == 409:
                        duplicatedBillyBills.append({
                            "cufe": parsed["cufe"],
                            "message": "Factura ya existía en Billy (409)"
                        })
                        # NO continue → CONTINUAMOS CON EL FLUJO NORMAL

                    # ---------- SI ES OTRO ERROR → FALLA ----------
                    elif r.status_code not in [200, 201]:
                        failedBills.append({
                            "cufe": parsed["cufe"],
                            "message": "Error al subir factura a Billy",
                            "status": r.status_code,
                            "details": r.text
                        })
                        continue

                except Exception as e:
                    failedBills.append({
                        "cufe": parsed["cufe"],
                        "message": f"Error al conectar con Billy: {str(e)}"
                    })
                    continue

                # -------------------- OBTENER EVENTOS (SIEMPRE) --------------------
                events = billEvents(parsed['cufe'], update=True)

                parsed['events'] = events['events']
                parsed['typeBill'] = events['type']
                parsed['currentOwner'] = events['currentOwner']
                if parsed['emitterId'] == events['current_ownerId']:
                    parsed['sameCurrentOwner'] = True
                else:
                    parsed['sameCurrentOwner'] = False

                # -------------------- PROCESAR ENDOSOS --------------------
                endorsedEvents = updateBillEvents(events['bill'])
                parsed['endorsed'] = len(endorsedEvents) > 0

                parsedBills.append(parsed)

            # -------------------- RESPUESTA FINAL --------------------
            return Response({
                "error": False,
                "bills": parsedBills,
                "duplicatedLocalBills": duplicatedLocalBills,
                "duplicatedBillyBills": duplicatedBillyBills,
                "failedBills": failedBills
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": True, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class readCreditNoteAV(BaseAV):
    @checkRole(['admin','third'])
    def post(self, request):
        parsedCreditNotes = []
        for file in request.FILES.getlist('creditNotes'):
            parsedCreditNotes.append(parseCreditNote(file))
        return response({'error': False, 'data': parsedCreditNotes}, 200)