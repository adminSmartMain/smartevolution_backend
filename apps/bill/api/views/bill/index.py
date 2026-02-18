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
            # -----------------------------
            # 1. Normalizar parámetros
            # -----------------------------
            params = {
                k: v if v != "" else None
                for k, v in request.query_params.items()
            }

            # -----------------------------
            # 2. Casos ESPECIALES (salida directa)
            # -----------------------------
            if params.get('billEvent'):
                bill = Bill.objects.get(id=params['billEvent'])
                serializer = (
                    BillEventReadOnlySerializer(bill)
                    if bill.cufe else
                    BillDetailSerializer(bill)
                )
                return response({'error': False, 'data': serializer.data}, 200)

            if params.get('payerId'):
                bill = Bill.objects.get(id=params['payerId'])
                client = Client.objects.get(document_number=bill.payerId)
                return response({'error': False, 'data': client.id}, 200)

            if params.get('reBuy'):
                op = PreOperation.objects.filter(
                    bill_id=params['reBuy']
                ).order_by('-opId').first()
                if not op:
                    return response({'error': True, 'message': 'No se encontraron operaciones'}, 404)
                serializer = PreOperationReadOnlySerializer(op)
                return response({'error': False, 'data': serializer.data}, 200)

            # -----------------------------
            # NUEVO CASO: bill_operation
            # -----------------------------
            if params.get('bill_operation') is not None:
                logger.debug('Caso: obtener factura para comprobar antes de crear operacion')

                bill_number = params.get('bill_operation')   # Ej: FE1113
                emitter_client_id = params.get('emitter')    # UUID del Client (viene del front)

                try:
                    # Validaciones mínimas
                    if not bill_number:
                        return response({'error': True, 'message': 'bill_operation es requerido'}, 400)

                    if not emitter_client_id:
                        return response({'error': True, 'message': 'emitter es requerido para buscar por número de factura'}, 400)

                    # Convertir UUID del emisor -> document_number (que es lo que guarda Bill.emitterId)
                    emitter_client = Client.objects.filter(document_number=emitter_client_id).only('document_number').first()
                    if not emitter_client or not emitter_client.document_number:
                        return response({'error': True, 'message': f'Emisor con ID {emitter_client_id} no encontrado'}, 404)

                    emitter_doc = emitter_client.document_number

                    # Buscar por combinación (billId + emitterId)
                    qs = Bill.objects.filter(billId=bill_number, emitterId=emitter_doc)

                    count = qs.count()
                    if count == 0:
                        return response({'error': True, 'message': 'Factura no encontrada'}, 404)

                    # Si por data sucia hay más de una, responde claro (en vez de reventar con get())
                    if count > 1:
                        logger.error(f"Ambigüedad: existen {count} facturas con billId={bill_number} y emitterId={emitter_doc}")
                        return response({
                            'error': True,
                            'message': 'Hay más de una factura con el mismo número para este emisor (data inconsistente).',
                            'detail': f'billId={bill_number}, emitterId={emitter_doc}, count={count}'
                        }, 409)

                    bill = qs.first()

                    # Serializar según CUFE
                    if bill.cufe:
                        logger.debug('Caso 43: con cufe')
                        serializer = BillEventReadOnlySerializer(bill)
                        return response({'error': False, 'data': serializer.data}, 200)

                    serializer = BillDetailSerializer(bill)
                    return response({'error': False, 'data': serializer.data}, 200)

                except Exception as e:
                    logger.error(f"Error buscando por bill_operation: {str(e)}", exc_info=True)
                    return response({'error': True, 'message': str(e)}, 400)

            # -----------------------------
            # 3. Queryset BASE
            # -----------------------------
            bills = Bill.objects.filter(state=1)

            # -----------------------------
            # 4. Filtros normales (DINÁMICOS)
            # -----------------------------
            if params.get('mode') == 'intelligent_query':
                # 🔍 Búsqueda inteligente
                if params.get('emitter_or_payer_or_billId'):
                    search = params['emitter_or_payer_or_billId']
                    bills = bills.filter(
                        Q(emitterName__icontains=search) |
                        Q(payerName__icontains=search) |
                        Q(billId__icontains=search)
                    )

                # 📄 typeBill
                if params.get('typeBill'):
                    bills = bills.filter(typeBill=params['typeBill'])

                # 📅 fechas
                if params.get('startDate') and params.get('endDate'):
                    bills = bills.filter(
                        created_at__gte=params['startDate'],
                        created_at__lte=params['endDate']
                    )

                # 🔌 channel
                if params.get('channel') == 'autogestion':
                    bills = bills.filter(
                        integrationCode__isnull=False
                    ).exclude(integrationCode='')
                elif params.get('channel') == 'no-autogestion':
                    bills = bills.filter(
                        Q(integrationCode__isnull=True) |
                        Q(integrationCode__exact='')
                    )

            # -----------------------------
            # 5. Filtros por operation (PreOperation)
            # -----------------------------
            if params.get('operation'):
                ops = PreOperation.objects.filter(opId=params['operation'])

                if params.get('startDate') and params.get('endDate'):
                    ops = ops.filter(
                        opDate__gte=params['startDate'],
                        opDate__lte=params['endDate']
                    )

                if params.get('typeBill'):
                    ops = ops.filter(bill__typeBill=params['typeBill'])

                if params.get('channel') == 'autogestion':
                    ops = ops.filter(
                        bill__integrationCode__isnull=False
                    ).exclude(bill__integrationCode='')
                elif params.get('channel') == 'no-autogestion':
                    ops = ops.filter(
                        Q(bill__integrationCode__isnull=True) |
                        Q(bill__integrationCode__exact='')
                    )

                bills = Bill.objects.filter(id__in=ops.values_list('bill_id', flat=True))

            # -----------------------------
            # 6. PK (cliente) - CASO ESPECIAL SIN PAGINACIÓN Y SIN updateMassiveTypeBill
            # -----------------------------
            if pk:
                try:
                    client = Client.objects.get(pk=pk)
                    bills = bills.filter(
                        Q(emitterId=pk) |
                        Q(emitterId=client.document_number)
                    )
                    
                    # ✅ OPCIÓN 1: Filtrar directamente en la consulta (RECOMENDADO)
                    # Filtramos solo facturas con currentBalance > 0 para optimizar
                    bills_with_balance = bills.filter(currentBalance__gt=0)
                    
                    # Serializar SOLO las facturas con saldo positivo
                    serializer = BillReadOnlySerializer(bills_with_balance, many=True)
                    
                    return response({
                        'error': False,
                        'data': serializer.data,
                        'count': bills_with_balance.count(),
                        'all_results': True,
                        'optimized_for_payer_filter': True
                    }, 200)
                    
                except Client.DoesNotExist:
                    return response({'error': False, 'data': []}, 200)

            # -----------------------------
            # 7. CASO GENERAL CON PAGINACIÓN (sin pk)
            # -----------------------------
            page = self.paginate_queryset(bills)
            if page is None:
                return response({'error': False, 'data': []}, 200)

            # -----------------------------
            # 8. updateMassiveTypeBill SOLO PARA CASO GENERAL
            # -----------------------------
            page_ids = [obj.id for obj in page]

            qs_page = Bill.objects.filter(id__in=page_ids)

            # ✅ Ejecutar actualización masiva y capturar warnings de Billy
            update_result = updateMassiveTypeBill(qs_page, billEvents)
            billy_warnings = (update_result or {}).get("warnings", [])

            # refrescar manteniendo orden
            refreshed = list(Bill.objects.filter(id__in=page_ids))
            ordered_page = sorted(refreshed, key=lambda x: page_ids.index(x.id))

            # -----------------------------
            # 9. SERIALIZACIÓN
            # -----------------------------
            serializer = BillReadOnlySerializer(ordered_page, many=True)

            # ✅ Response paginado normal
            resp = self.get_paginated_response(serializer.data)

            # ✅ Agregar mensaje de advertencia para el frontend si Billy falló
            if billy_warnings:
                resp.data["billy_warning"] = True
                resp.data["billy_warning_message"] = (
                    f"Billy está lento o no respondió correctamente. "
                    f"{len(billy_warnings)} facturas no pudieron actualizar eventos. "
                    "No se realizaron cambios sobre esas facturas."
                )
                resp.data["warnings"] = billy_warnings
            else:
                resp.data["billy_warning"] = False

            return resp


        except Exception as e:
            logger.error("Error en /api/bill/", exc_info=True)
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
                logger.debug(f'Eventos obtenidos de Billy para CUFE {parsed["cufe"]}: {events}')
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