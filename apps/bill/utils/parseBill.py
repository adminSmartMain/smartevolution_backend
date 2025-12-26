import untangle

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
    parsedXml = {}

    try:
        xml = untangle.parse(file)

        # ---------------------------------------------------------
        # CASO 1 → El XML viene dentro de AttachedDocument
        # ---------------------------------------------------------
        if hasattr(xml, 'AttachedDocument') and hasattr(xml.AttachedDocument, 'cac_Attachment'):

            try:
                xml2 = untangle.parse(
                    xml.AttachedDocument.cac_Attachment.cac_ExternalReference.cbc_Description.cdata
                )

                # -------------------- IVA --------------------
                total_tax_amount = 0
                if hasattr(xml2.Invoice, 'cac_TaxTotal'):
                    tax_totals = xml2.Invoice.cac_TaxTotal

                    if isinstance(tax_totals, list):
                        for t in tax_totals:
                            total_tax_amount += float(t.cbc_TaxAmount.cdata)
                    else:
                        total_tax_amount = float(tax_totals.cbc_TaxAmount.cdata)

                parsedXml['iva'] = total_tax_amount

                # -------------------- CAMPOS BÁSICOS --------------------
                parsedXml['billId'] = xml2.Invoice.cbc_ID.cdata
                parsedXml['emitterName'] = xml2.Invoice.cac_AccountingSupplierParty.cac_Party.cac_PartyTaxScheme.cbc_RegistrationName.cdata
                parsedXml['emitterId'] = xml2.Invoice.cac_AccountingSupplierParty.cac_Party.cac_PartyTaxScheme.cbc_CompanyID.cdata
                parsedXml['payerName'] = xml2.Invoice.cac_AccountingCustomerParty.cac_Party.cac_PartyTaxScheme.cbc_RegistrationName.cdata
                parsedXml['payerId'] = xml2.Invoice.cac_AccountingCustomerParty.cac_Party.cac_PartyTaxScheme.cbc_CompanyID.cdata

                parsedXml['billValue'] = float(xml2.Invoice.cac_LegalMonetaryTotal.cbc_LineExtensionAmount.cdata)
                parsedXml['subTotal'] = parsedXml['billValue'] + parsedXml['iva']
                parsedXml['total'] = parsedXml['subTotal']

                parsedXml['dateBill'] = xml2.Invoice.cbc_IssueDate.cdata

                try:
                    parsedXml['datePayment'] = xml2.Invoice.cac_PaymentMeans.cbc_PaymentDueDate.cdata
                except:
                    parsedXml['datePayment'] = None

                parsedXml['cufe'] = xml2.Invoice.cbc_UUID.cdata

                try:
                    parsedXml['expirationDate'] = xml2.Invoice.cbc_DueDate.cdata
                except:
                    parsedXml['expirationDate'] = None

                return parsedXml

            except Exception as e:
                return {'error': True, 'message': f"Error processing AttachedDocument: {str(e)}"}

        # ---------------------------------------------------------
        # CASO 2 → El XML viene directamente como Invoice
        # ---------------------------------------------------------
        elif hasattr(xml, 'Invoice'):

            try:
                xml2 = xml

                # -------------------- IVA --------------------
                total_tax_amount = 0
                if hasattr(xml2.Invoice, 'cac_TaxTotal'):
                    tax_totals = xml2.Invoice.cac_TaxTotal

                    if isinstance(tax_totals, list):
                        for t in tax_totals:
                            total_tax_amount += float(t.cbc_TaxAmount.cdata)
                    else:
                        total_tax_amount = float(tax_totals.cbc_TaxAmount.cdata)

                parsedXml['iva'] = total_tax_amount

                # -------------------- EXTRAER EXTENSIONES UBL --------------------
                try:
                    for extension in xml2.Invoice.ext_UBLExtensions.ext_UBLExtension:
                        if hasattr(extension, "ext_ExtensionContent"):
                            content = extension.ext_ExtensionContent

                            if hasattr(content, "sts_DianExtensions"):
                                dian_ext = content.sts_DianExtensions

                                if hasattr(dian_ext, "sts_InvoiceControl") and hasattr(dian_ext.sts_InvoiceControl, "sts_AuthorizedInvoices"):
                                    authorized = dian_ext.sts_InvoiceControl.sts_AuthorizedInvoices

                                    prefix = authorized.sts_Prefix.cdata if hasattr(authorized, "sts_Prefix") else None
                                    from_value = authorized.sts_From.cdata if hasattr(authorized, "sts_From") else None

                                    parsedXml['prefix'] = prefix
                                    parsedXml['fromAuthorized'] = from_value

                except Exception as e:
                    logger.debug(f"Error procesando UBLExtensions: {e}")

                # -------------------- CAMPOS BÁSICOS --------------------
                parsedXml['billId'] = xml2.Invoice.cbc_ID.cdata
                parsedXml['emitterName'] = xml2.Invoice.cac_AccountingSupplierParty.cac_Party.cac_PartyTaxScheme.cbc_RegistrationName.cdata
                parsedXml['emitterId'] = xml2.Invoice.cac_AccountingSupplierParty.cac_Party.cac_PartyTaxScheme.cbc_CompanyID.cdata

                parsedXml['payerName'] = xml2.Invoice.cac_AccountingCustomerParty.cac_Party.cac_PartyTaxScheme.cbc_RegistrationName.cdata
                parsedXml['payerId'] = xml2.Invoice.cac_AccountingCustomerParty.cac_Party.cac_PartyTaxScheme.cbc_CompanyID.cdata

                parsedXml['billValue'] = float(xml2.Invoice.cac_LegalMonetaryTotal.cbc_LineExtensionAmount.cdata)
                parsedXml['subTotal'] = parsedXml['billValue'] + parsedXml['iva']
                parsedXml['total'] = parsedXml['subTotal']

                parsedXml['dateBill'] = xml2.Invoice.cbc_IssueDate.cdata

                try:
                    parsedXml['datePayment'] = xml2.Invoice.cac_PaymentMeans.cbc_PaymentDueDate.cdata
                except:
                    parsedXml['datePayment'] = None

                parsedXml['cufe'] = xml2.Invoice.cbc_UUID.cdata

                try:
                    parsedXml['expirationDate'] = xml2.Invoice.cbc_DueDate.cdata
                except:
                    parsedXml['expirationDate'] = None

                return parsedXml

            except Exception as e:
                return {'error': True, 'message': f"Error processing Invoice: {str(e)}"}

        # ---------------------------------------------------------
        # SIN AttachedDocument NI Invoice
        # ---------------------------------------------------------
        else:
            return {'error': True, 'message': 'AttachedDocument o Invoice no encontrados'}

    except Exception as e:
        return {'error': True, 'message': f"Error parsing XML: {str(e)}"}

