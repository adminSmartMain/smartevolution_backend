from django.db.models import Q
# Serializers
from apps.bill.api.serializers.index import BillSerializer, BillReadOnlySerializer, BillEventReadOnlySerializer
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

            if len(request.query_params) > 0:
                if request.query_params.get('emitter') != None:
                    bills = Bill.objects.filter(emitterName__icontains=request.query_params.get('emitter'))
                elif request.query_params.get('payer') != None:
                    bills = Bill.objects.filter(payerName__icontains=request.query_params.get('payer'))
                elif request.query_params.get('opId') != None:
                    billList = []
                    # get the bills of the operation
                    # get the opId
                    opId = PreOperation.objects.get(id=request.query_params.get('opId'))
                    op   = PreOperation.objects.filter(opId=opId.opId)
                    for x in op:
                        bills = Bill.objects.get(id=x.bill.id)
                        billList.append({
                            'id': bills.id,
                            'billId': bills.billId,
                            'total': bills.total,
                            'opAmount': x.payedAmount,
                            'opExpiration':x.opExpiration,
                            'dateBill': x.opDate
                        })                   
                    return response({'error': False, 'data': billList}, 200)

                elif request.query_params.get('bill') != None:
                    bills = Bill.objects.filter(billId__icontains=request.query_params.get('bill'))
                
                elif request.query_params.get('operation') != None:
                    billList = []
                    # get the bills of the operation
                    op   = PreOperation.objects.filter(opId=request.query_params.get('operation'))
                    for x in op:
                        bill = Bill.objects.get(id=x.bill.id)
                        billList.append(bill)
                    page       = self.paginate_queryset(billList)
                    if page is not None:
                        serializer = BillReadOnlySerializer(page, many=True)
                        return self.get_paginated_response(serializer.data)
                elif request.query_params.get('payerId') != None:
                    # get the payer of the bill
                    try:
                        bill   = Bill.objects.get(id=request.query_params.get('payerId'))
                        client = Client.objects.get(document_number=bill.payerId)
                        return response({'error': False, 'data': client.id}, 200)
                    except:
                        return response({'error': True, 'message': 'Pagador no Registrado'}, 400)

                elif request.query_params.get('reBuy') != None:
                    bill = PreOperation.objects.filter(bill_id=request.query_params.get('reBuy')).order_by('-opId').first()
                    serializer = PreOperationReadOnlySerializer(bill)
                    return response({'error': False, 'data': serializer.data}, 200)
                
                elif request.query_params.get('billEvent') != None:
                    # Get the bill
                    bill = Bill.objects.get(id=request.query_params.get('billEvent'))
                    if bill.cufe:
                        serializer = BillEventReadOnlySerializer(bill)
                        return response({'error': False, 'data':serializer.data}, 200)
                    else:
                        serializer = BillReadOnlySerializer(bill)
                        return response({'error': True, 'data': serializer.data}, 200)
                else:
                    bills = Bill.objects.filter(state=1)
                page       = self.paginate_queryset(bills)
                if page is not None:
                    serializer = BillReadOnlySerializer(page, many=True)
                    return self.get_paginated_response(serializer.data)


            if pk:
                client = Client.objects.get(pk=pk)
                bill = Bill.objects.filter(
                    Q(emitterId=pk) | Q(emitterId=client.document_number))
                serializer = BillReadOnlySerializer(bill, many=True)
                return response({'error': False, 'data': serializer.data}, 200)
            else:
                bills = Bill.objects.filter(state=1)
                page       = self.paginate_queryset(bills)
                if page is not None:
                    serializer = BillReadOnlySerializer(page, many=True)
                    return self.get_paginated_response(serializer.data)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

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

