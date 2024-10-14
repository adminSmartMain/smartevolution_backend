import untangle
from .billEvents import billEvents
from .updateBillEvents import billEvents as updateBillEvents

def parseBill(file):
    parsedXml = {}
    xml = untangle.parse(file) #convierte los nodos del xml en atributos
    try:
        try:
            #Caso en el que los la factura posee el nodo atttachment Document y ya no falla
            xml2 = untangle.parse(xml.AttachedDocument.cac_Attachment.cac_ExternalReference.cbc_Description.cdata)
            parsedXml['billId']      = xml2.Invoice.cbc_ID.cdata
            parsedXml['emitterName'] = xml2.Invoice.cac_AccountingSupplierParty.cac_Party.cac_PartyTaxScheme.cbc_RegistrationName.cdata
            parsedXml['emitterId']   = xml2.Invoice.cac_AccountingSupplierParty.cac_Party.cac_PartyTaxScheme.cbc_CompanyID.cdata
            parsedXml['payerName']   = xml2.Invoice.cac_AccountingCustomerParty.cac_Party.cac_PartyTaxScheme.cbc_RegistrationName.cdata
            parsedXml['payerId']     = xml2.Invoice.cac_AccountingCustomerParty.cac_Party.cac_PartyTaxScheme.cbc_CompanyID.cdata
            parsedXml['billValue']   = float(xml2.Invoice.cac_LegalMonetaryTotal.cbc_LineExtensionAmount.cdata)
            try:
                parsedXml['iva']         = float(xml2.Invoice.cac_TaxTotal.cbc_TaxAmount.cdata)
            except:
                parsedXml['iva']         = 0
            parsedXml['subTotal']    = float(parsedXml['billValue'] + parsedXml['iva'])
            parsedXml['total']       = float(parsedXml['subTotal'])
            parsedXml['dateBill']    = xml2.Invoice.cbc_IssueDate.cdata
            try:
                parsedXml['datePayment'] = xml2.Invoice.cac_PaymentMeans.cbc_PaymentDueDate.cdata
            except:
                parsedXml['datePayment'] = None 
            parsedXml['cufe']        = xml2.Invoice.cbc_UUID.cdata

            try:
                parsedXml['expirationDate'] = xml2.Invoice.cbc_DueDate.cdata 
            except:
                pass
            
            # get bill events
            try:
                events = billEvents(parsedXml['cufe'],update=True)

                # Validar si el tipo devuelto es 'error'
                if events['type'] == 'error':
                    raise Exception("Error type returned from billEvents")
                
                parsedXml['typeBill'] = events['type']
                parsedXml['events']   = events['events']
                parsedXml['file']     = file
                events['currentOwner'] = events['currentOwner'].strip()
                # check if the current owner is the same as the emitter
                if parsedXml['emitterName'] == events['currentOwner']:
                    parsedXml['sameCurrentOwner'] = True
                else:
                    parsedXml['sameCurrentOwner'] = False

                getEndorsed = updateBillEvents(events['bill'])
                if getEndorsed != None:
                    valid  = False
                    # check if the bill has the events  f5d475c0-4433-422f-b3d2-7964ea0aa5c4 and 3bb86c74-1d1c-4986-a905-a47624b09322
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

                    if valid:
                        parsedXml['endorsed'] = True
                    else:
                        parsedXml['endorsed'] = False  

                    parsedXml['currentOwner'] = events['currentOwner']
            except Exception as e:
                parsedXml['endorsed']     = False
                parsedXml['events']       = []
                try:
                    parsedXml['currentOwner'] = events['emitterName'] # se agregó un try except con el fin de conservar codigo y que podamos volver a reutilizar cuando el tema del cufe esté solucionado
                    
                except:
                    parsedXml['currentOwner'] = parsedXml['emitterName'] ## acá estaba el problema, al no tener la posibilidad de usar el cufe esta linea usaba el objeto event, asi que de manera eventual se toma el mismo'emitterName' del xml ya que este debe coincidir con el obtenido en el cufe. Este se obtiene en la linea 90 de bill Events. 
                parsedXml['typeBill']     = 'fdb5feb4-24e9-41fc-9689-31aff60b76c9'
            return parsedXml
        except Exception as e:
            #este es el caso donde los xml solo tienen los nodos Invoice
            parsedXml['billId']      = xml.Invoice.cbc_ID.cdata
            parsedXml['emitterName'] = xml.Invoice.cac_AccountingSupplierParty.cac_Party.cac_PartyTaxScheme.cbc_RegistrationName.cdata
            parsedXml['emitterId']   = xml.Invoice.cac_AccountingSupplierParty.cac_Party.cac_PartyTaxScheme.cbc_CompanyID.cdata
            parsedXml['payerName']   = xml.Invoice.cac_AccountingCustomerParty.cac_Party.cac_PartyTaxScheme.cbc_RegistrationName.cdata
            parsedXml['payerId']     = xml.Invoice.cac_AccountingCustomerParty.cac_Party.cac_PartyTaxScheme.cbc_CompanyID.cdata
            parsedXml['billValue']   = float(xml.Invoice.cac_LegalMonetaryTotal.cbc_LineExtensionAmount.cdata)
            try:
                parsedXml['iva']         = float(xml.Invoice.cac_TaxTotal.cbc_TaxAmount.cdata)
            except:
                parsedXml['iva']         = 0
            parsedXml['subTotal']    = float(parsedXml['billValue'] + parsedXml['iva'])
            parsedXml['total']       = float(parsedXml['subTotal'])
            parsedXml['dateBill']    = xml.Invoice.cbc_IssueDate.cdata
            try:
                parsedXml['datePayment'] = xml.Invoice.cac_PaymentMeans.cbc_PaymentDueDate.cdata
            except:
                parsedXml['datePayment'] = None 
            
            parsedXml['cufe']        = xml.Invoice.cbc_UUID.cdata

            try:
                parsedXml['expirationDate'] = xml.Invoice.cbc_DueDate.cdata 
            except:
                pass
            
            # get bill events
            try:
                events = billEvents(parsedXml['cufe'])
                parsedXml['typeBill'] = events['type']
                parsedXml['events']   = events['events']
                parsedXml['file']     = file
                events['currentOwner'] = events['currentOwner'].strip()
                # check if the current owner is the same as the emitter
                if parsedXml['emitterName'] == events['currentOwner']:
                    parsedXml['sameCurrentOwner'] = True
                else:
                    parsedXml['sameCurrentOwner'] = False
                getEndorsed = updateBillEvents(events['bill'])
                valid  = False
                # check if the bill has the events  f5d475c0-4433-422f-b3d2-7964ea0aa5c4 and 3bb86c74-1d1c-4986-a905-a47624b09322
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

                if valid:
                    parsedXml['endorsed'] = True
                else:
                    parsedXml['endorsed'] = False

                parsedXml['currentOwner'] = events['currentOwner']
            except:
                parsedXml['endorsed']     = False
                parsedXml['events']       = []
                try:
                    parsedXml['currentOwner'] = events['emitterName'] #acá se hizo lo mismo que para el caso de los nodos attachmentData
                except:
                    parsedXml['currentOwner'] =  parsedXml['emitterName']
                    
                parsedXml['typeBill']     = 'fdb5feb4-24e9-41fc-9689-31aff60b76c9'
            return parsedXml
    except Exception as e:
        return {'error': True, 'message': str(e)}