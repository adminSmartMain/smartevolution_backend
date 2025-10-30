import untangle
from .billEvents import billEvents
from .updateBillEvents import billEvents as updateBillEvents
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

def parseBill(file):
    # Diccionario para almacenar los datos procesados
    parsedXml = {}
    
    try:
        # Parseamos el archivo XML con la librería untangle
        xml = untangle.parse(file)

        # Verificar si el XML contiene el nodo 'AttachedDocument'
        if hasattr(xml, 'AttachedDocument') and hasattr(xml.AttachedDocument, 'cac_Attachment'):
           
            
            try:
               
                # Si existe, parseamos el XML dentro del 'AttachedDocument' para obtener más información
                xml2 = untangle.parse(
                    xml.AttachedDocument.cac_Attachment.cac_ExternalReference.cbc_Description.cdata
                )
                
                # Inicializamos una variable para acumular los valores de 'cbc:TaxAmount'
                total_tax_amount = 0

                # Verificamos si el nodo 'Invoice' tiene el nodo 'cac_TaxTotal'
                if hasattr(xml2.Invoice, 'cac_TaxTotal'):
                    tax_totals = xml2.Invoice.cac_TaxTotal
                    
                    # Si hay múltiples nodos 'cac_TaxTotal', los procesamos en una lista
                    if isinstance(tax_totals, list):
                        for tax_total in tax_totals:
                            # Sumamos el valor de 'cbc:TaxAmount' a 'total_tax_amount'
                            tax_amount = float(tax_total.cbc_TaxAmount.cdata)
                            total_tax_amount += tax_amount
                    else:  # Si solo hay un nodo 'cac_TaxTotal'
                        total_tax_amount = float(tax_totals.cbc_TaxAmount.cdata)

                    # Almacenamos el valor acumulado en 'parsedXml['iva']'
                    parsedXml['iva'] = total_tax_amount
                else:
                    # Si no se encuentra 'cac_TaxTotal', se asigna 0
                    parsedXml['iva'] = 0

                # Resto de los datos del XML que necesitamos extraer
                parsedXml['billId'] = xml2.Invoice.cbc_ID.cdata
                parsedXml['emitterName'] = xml2.Invoice.cac_AccountingSupplierParty.cac_Party.cac_PartyTaxScheme.cbc_RegistrationName.cdata
                parsedXml['emitterId'] = xml2.Invoice.cac_AccountingSupplierParty.cac_Party.cac_PartyTaxScheme.cbc_CompanyID.cdata
                parsedXml['payerName'] = xml2.Invoice.cac_AccountingCustomerParty.cac_Party.cac_PartyTaxScheme.cbc_RegistrationName.cdata
                parsedXml['payerId'] = xml2.Invoice.cac_AccountingCustomerParty.cac_Party.cac_PartyTaxScheme.cbc_CompanyID.cdata
                parsedXml['billValue'] = float(xml2.Invoice.cac_LegalMonetaryTotal.cbc_LineExtensionAmount.cdata)

                # Tratamos de obtener el IVA (si existe), sino, lo asignamos como 0
                try:
                    parsedXml['iva'] = float(xml2.Invoice.cac_TaxTotal.cbc_TaxAmount.cdata)
                except:
                    parsedXml['iva'] = 0

                # Calculamos el subTotal y el total de la factura
                parsedXml['subTotal'] = parsedXml['billValue'] + parsedXml['iva']
                parsedXml['total'] = parsedXml['subTotal']

                # Obtenemos las fechas de la factura
                parsedXml['dateBill'] = xml2.Invoice.cbc_IssueDate.cdata
                try:
                    parsedXml['datePayment'] = xml2.Invoice.cac_PaymentMeans.cbc_PaymentDueDate.cdata
                except:
                    parsedXml['datePayment'] = None 

                # Almacenamos el CUFE de la factura
                parsedXml['cufe'] = xml2.Invoice.cbc_UUID.cdata

                # Verificamos si existe la fecha de vencimiento (expirationDate)
                try:
                    parsedXml['expirationDate'] = xml2.Invoice.cbc_DueDate.cdata 
                except:
                    pass

                # Obtener eventos relacionados con la factura
                try:
                    events = billEvents(parsedXml['cufe'], update=True)

                    # Validar si el tipo de evento es 'error'
                    if events['type'] == 'error':
                        raise Exception("Error type returned from billEvents")
                    
                    # Almacenamos los eventos y el tipo de factura
                    parsedXml['typeBill'] = events['type']
                    parsedXml['events'] = events['events']
                    parsedXml['file'] = file
                    events['currentOwner'] = events['currentOwner'].strip()

                    # Verificamos si el propietario actual es el mismo que el emisor
                    if parsedXml['emitterName'] == events['currentOwner']:
                        parsedXml['sameCurrentOwner'] = True
                    else:
                        parsedXml['sameCurrentOwner'] = False

                    # Obtenemos la información de los eventos actualizados
                    getEndorsed = updateBillEvents(events['bill'])
                    valid = False

                    # Verificamos si los eventos de la factura contienen ciertos valores
                    for event in getEndorsed:
                        if event['event'] == '3ea77762-7208-457a-b035-70069ee42b5e':
                            valid = True
                            parsedXml['typeBill'] = '29113618-6ab8-4633-aa8e-b3d6f242e8a4'
                            break
                        if event['event'] == '3bb86c74-1d1c-4986-a905-a47624b09322':
                            valid = True
                            parsedXml['typeBill'] = '29113618-6ab8-4633-aa8e-b3d6f242e8a4'
                            break
                        if event['event'] == '0e333b6b-27b1-4aaf-87ce-ad60af6e52e6':
                            valid = True
                            parsedXml['typeBill'] = '29113618-6ab8-4633-aa8e-b3d6f242e8a4'
                            break

                    # Marcamos la factura como 'endorsed' si es válida
                    if valid:
                        parsedXml['endorsed'] = True
                    else:
                        parsedXml['endorsed'] = False  

                    parsedXml['currentOwner'] = events['currentOwner']
                except Exception as e:
                    parsedXml['endorsed'] = False
                    parsedXml['events'] = []
                    try:
                        # Si ocurre un error, intentamos obtener el 'currentOwner' del evento
                        parsedXml['currentOwner'] = events['emitterName']
                    except:
                        parsedXml['currentOwner'] = "No disponible"
                    
                    # Si no hay eventos, marcamos el tipo de factura como 'error'
                    parsedXml['typeBill'] = 'fdb5feb4-24e9-41fc-9689-31aff60b76c9'

                return parsedXml
            except Exception as e:
                # En caso de error al procesar 'AttachedDocument', retornamos el error
                return {'error': True, 'message': f"Error processing AttachedDocument: {str(e)}"}
        elif hasattr(xml, 'Invoice'):
            xml = untangle.parse(file)

            try:
               
                # Si existe, parseamos el XML dentro del 'AttachedDocument' para obtener más información
              
                xml2 = xml
               
                # Inicializamos una variable para acumular los valores de 'cbc:TaxAmount'
                total_tax_amount = 0

                # Verificamos si el nodo 'Invoice' tiene el nodo 'cac_TaxTotal'
                if hasattr(xml2.Invoice, 'cac_TaxTotal'):
                  
                    tax_totals = xml2.Invoice.cac_TaxTotal
                    
                    # Si hay múltiples nodos 'cac_TaxTotal', los procesamos en una lista
                    if isinstance(tax_totals, list):
                        
                        for tax_total in tax_totals:
                            # Sumamos el valor de 'cbc:TaxAmount' a 'total_tax_amount'
                            tax_amount = float(tax_total.cbc_TaxAmount.cdata)
                            total_tax_amount += tax_amount
                    else:  # Si solo hay un nodo 'cac_TaxTotal'
                       
                        total_tax_amount = float(tax_totals.cbc_TaxAmount.cdata)
                       
                    # Almacenamos el valor acumulado en 'parsedXml['iva']'
                   
                    parsedXml['iva'] = total_tax_amount
                   
                else:
                    # Si no se encuentra 'cac_TaxTotal', se asigna 0
                   
                    parsedXml['iva'] = 0
                   
                # Resto de los datos del XML que necesitamos extraer
                
                
               # Iterar sobre todas las extensiones UBLExtension
                for extension in xml2.Invoice.ext_UBLExtensions.ext_UBLExtension:
                    try:
                        # Verificar si tiene contenido dentro de ext:ExtensionContent
                        if hasattr(extension, "ext_ExtensionContent"):
                            content = extension.ext_ExtensionContent

                            # Buscar sts:DianExtensions dentro de ExtensionContent
                            if hasattr(content, "sts_DianExtensions"):
                                dian_extensions = content.sts_DianExtensions

                                # Buscar sts:InvoiceControl dentro de DianExtensions
                                if hasattr(dian_extensions, "sts_InvoiceControl"):
                                    invoice_control = dian_extensions.sts_InvoiceControl

                                    # Buscar sts:AuthorizedInvoices dentro de InvoiceControl
                                    if hasattr(invoice_control, "sts_AuthorizedInvoices"):
                                        authorized_invoices = invoice_control.sts_AuthorizedInvoices

                                        # Extraer valores de Prefix y From si existen
                                        prefix = authorized_invoices.sts_Prefix.cdata if hasattr(authorized_invoices, "sts_Prefix") else None
                                        from_value = authorized_invoices.sts_From.cdata if hasattr(authorized_invoices, "sts_From") else None

                                        # Registrar los resultados
                                     
                    except Exception as e:
                        logger.debug(f"Error procesando una extensión: {e}")
                
               
                parsedXml['billId'] = xml2.Invoice.cbc_ID.cdata
 
                parsedXml['emitterName'] = xml2.Invoice.cac_AccountingSupplierParty.cac_Party.cac_PartyTaxScheme.cbc_RegistrationName.cdata

                parsedXml['emitterId'] = xml2.Invoice.cac_AccountingSupplierParty.cac_Party.cac_PartyTaxScheme.cbc_CompanyID.cdata
              
                parsedXml['payerName'] = xml2.Invoice.cac_AccountingCustomerParty.cac_Party.cac_PartyTaxScheme.cbc_RegistrationName.cdata
              
                parsedXml['payerId'] = xml2.Invoice.cac_AccountingCustomerParty.cac_Party.cac_PartyTaxScheme.cbc_CompanyID.cdata
               
                parsedXml['billValue'] = float(xml2.Invoice.cac_LegalMonetaryTotal.cbc_LineExtensionAmount.cdata)
               
                # Tratamos de obtener el IVA (si existe), sino, lo asignamos como 0
                try:
                  
                    parsedXml['iva'] = float(xml2.Invoice.cac_TaxTotal.cbc_TaxAmount.cdata)
                  
                except:
                   
                    parsedXml['iva'] = 0
             
                # Calculamos el subTotal y el total de la factura
                parsedXml['subTotal'] = parsedXml['billValue'] + parsedXml['iva']
               
                parsedXml['total'] = parsedXml['subTotal']
              
                # Obtenemos las fechas de la factura
                parsedXml['dateBill'] = xml2.Invoice.cbc_IssueDate.cdata
       
                try:
                    parsedXml['datePayment'] = xml2.Invoice.cac_PaymentMeans.cbc_PaymentDueDate.cdata
               
                except:
                  
                    parsedXml['datePayment'] = None 
                    

                # Almacenamos el CUFE de la factura
               
                parsedXml['cufe'] = xml2.Invoice.cbc_UUID.cdata
                
                # Verificamos si existe la fecha de vencimiento (expirationDate)
                try:
                    
                    parsedXml['expirationDate'] = xml2.Invoice.cbc_DueDate.cdata 
                    
                except:
                    pass

                # Obtener eventos relacionados con la factura
                try:
                    
                    events = billEvents(parsedXml['cufe'], update=True)
                  
                    # Validar si el tipo de evento es 'error'
                    if events['type'] == 'error':
                        raise Exception("Error type returned from billEvents")
                    
                    # Almacenamos los eventos y el tipo de factura
                   
                    parsedXml['typeBill'] = events['type']
                    
                    parsedXml['events'] = events['events']
                    
                    parsedXml['file'] = file
                    
                    events['currentOwner'] = events['currentOwner'].strip()
                    
                    # Verificamos si el propietario actual es el mismo que el emisor
                    if parsedXml['emitterName'] == events['currentOwner']:
                        
                        parsedXml['sameCurrentOwner'] = True
                        
                    else:
                        parsedXml['sameCurrentOwner'] = False

                    # Obtenemos la información de los eventos actualizados
                    
                    getEndorsed = updateBillEvents(events['bill'])
                  
                    valid = False
                   
                    # Verificamos si los eventos de la factura contienen ciertos valores
                    for event in getEndorsed:
                        if event['event'] == '3ea77762-7208-457a-b035-70069ee42b5e':
                            valid = True
                            parsedXml['typeBill'] = '29113618-6ab8-4633-aa8e-b3d6f242e8a4'
                            break
                        if event['event'] == '3bb86c74-1d1c-4986-a905-a47624b09322':
                            valid = True
                            parsedXml['typeBill'] = '29113618-6ab8-4633-aa8e-b3d6f242e8a4'
                            break
                        if event['event'] == '0e333b6b-27b1-4aaf-87ce-ad60af6e52e6':
                            valid = True
                            parsedXml['typeBill'] = '29113618-6ab8-4633-aa8e-b3d6f242e8a4'
                            break
                   
                    # Marcamos la factura como 'endorsed' si es válida
                    if valid:
                        parsedXml['endorsed'] = True
                    else:
                        parsedXml['endorsed'] = False  

                    parsedXml['currentOwner'] = events['currentOwner']
                except Exception as e:
                    parsedXml['endorsed'] = False
                    parsedXml['events'] = []
                    try:
                        # Si ocurre un error, intentamos obtener el 'currentOwner' del evento
                        parsedXml['currentOwner'] = events['emitterName']
                       
                    except:
                        parsedXml['currentOwner'] = "No disponible"
                    
                    # Si no hay eventos, marcamos el tipo de factura como 'error'
                    parsedXml['typeBill'] = 'fdb5feb4-24e9-41fc-9689-31aff60b76c9'
                  
                return parsedXml
            except Exception as e:
                # En caso de error al procesar 'AttachedDocument', retornamos el error
                return {'error': True, 'message': f"Error processing AttachedDocument: {str(e)}"}
            
        else:
            # Si no se encuentra 'AttachedDocument', se retorna un error
            return {'error': True, 'message': 'AttachedDocument or cac_Attachment not found or Invoice'}

    except Exception as e:
        # Capturamos cualquier otro error durante el parseo del XML
        return {'error': True, 'message': f"Error parsing XML: {str(e)}"}
