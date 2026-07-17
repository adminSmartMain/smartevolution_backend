import logging
import untangle

# Configurar el logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Evita duplicar handlers si Django recarga el módulo
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)


def clean_embedded_xml(xml_text):
    """
    Limpia XML embebido dentro de CDATA.

    Algunos proveedores envían el Invoice así:
        <![CDATA[
            <?xml version="1.0" encoding="UTF-8"?><Invoice...
        ]]>

    Si hay espacios o saltos de línea antes de <?xml, untangle falla con:
        XML or text declaration not at start of entity

    Por eso usamos strip().
    """
    if xml_text is None:
        return ""

    return xml_text.strip()


def get_tax_total(invoice):
    """
    Suma todos los TaxTotal del Invoice.
    Sirve tanto si cac_TaxTotal viene como lista como si viene como objeto único.
    """
    total_tax_amount = 0

    try:
        if not hasattr(invoice, "cac_TaxTotal"):
            return 0

        tax_totals = invoice.cac_TaxTotal

        if isinstance(tax_totals, list):
            for tax in tax_totals:
                try:
                    total_tax_amount += float(tax.cbc_TaxAmount.cdata)
                except Exception as e:
                    logger.debug(f"No se pudo leer un TaxAmount: {e}")
        else:
            total_tax_amount = float(tax_totals.cbc_TaxAmount.cdata)

    except Exception as e:
        logger.debug(f"Error leyendo impuestos: {e}")
        total_tax_amount = 0

    return total_tax_amount


def extract_ubl_extensions(invoice, parsedXml):
    """
    Extrae datos opcionales de UBLExtensions:
    - prefix
    - fromAuthorized

    Si no existen, no rompe el proceso.
    """
    try:
        if not hasattr(invoice, "ext_UBLExtensions"):
            return

        extensions = invoice.ext_UBLExtensions.ext_UBLExtension

        if not isinstance(extensions, list):
            extensions = [extensions]

        for extension in extensions:
            if not hasattr(extension, "ext_ExtensionContent"):
                continue

            content = extension.ext_ExtensionContent

            if not hasattr(content, "sts_DianExtensions"):
                continue

            dian_ext = content.sts_DianExtensions

            if not hasattr(dian_ext, "sts_InvoiceControl"):
                continue

            invoice_control = dian_ext.sts_InvoiceControl

            if not hasattr(invoice_control, "sts_AuthorizedInvoices"):
                continue

            authorized = invoice_control.sts_AuthorizedInvoices

            parsedXml["prefix"] = (
                authorized.sts_Prefix.cdata
                if hasattr(authorized, "sts_Prefix")
                else None
            )

            parsedXml["fromAuthorized"] = (
                authorized.sts_From.cdata
                if hasattr(authorized, "sts_From")
                else None
            )

    except Exception as e:
        logger.debug(f"Error procesando UBLExtensions: {e}")


def get_payment_due_date(invoice):
    """
    Obtiene la fecha de vencimiento desde cac:PaymentMeans/cbc:PaymentDueDate.

    Untangle devuelve una lista cuando el XML contiene varios PaymentMeans.
    Por eso se normaliza el valor a lista y se toma la primera fecha válida.
    """
    payment_means = getattr(invoice, "cac_PaymentMeans", None)

    if payment_means is None:
        return None

    if not isinstance(payment_means, list):
        payment_means = [payment_means]

    due_dates = []

    for payment_mean in payment_means:
        due_date_node = getattr(payment_mean, "cbc_PaymentDueDate", None)
        due_date = getattr(due_date_node, "cdata", None)

        if due_date:
            due_dates.append(due_date.strip())

    unique_due_dates = list(dict.fromkeys(due_dates))

    if len(unique_due_dates) > 1:
        logger.warning(
            "La factura contiene varias fechas de vencimiento: %s. "
            "Se utilizará la primera.",
            unique_due_dates,
        )

    return unique_due_dates[0] if unique_due_dates else None


def get_expiration_date(invoice):
    """
    Intenta leer cbc:DueDate y, si no existe, usa PaymentDueDate.
    En las facturas DIAN analizadas la fecha suele venir en PaymentMeans.
    """
    due_date_node = getattr(invoice, "cbc_DueDate", None)
    due_date = getattr(due_date_node, "cdata", None)

    if due_date:
        return due_date.strip()

    return get_payment_due_date(invoice)


def parse_invoice(invoice):
    """
    Recibe directamente el nodo Invoice ya parseado por untangle.
    Extrae los campos que usa el sistema.
    """
    parsedXml = {}

    # -------------------- IVA --------------------
    parsedXml["iva"] = get_tax_total(invoice)

    # -------------------- EXTENSIONES UBL --------------------
    extract_ubl_extensions(invoice, parsedXml)

    # -------------------- CAMPOS BÁSICOS --------------------
    parsedXml["billId"] = invoice.cbc_ID.cdata

    parsedXml["emitterName"] = (
        invoice
        .cac_AccountingSupplierParty
        .cac_Party
        .cac_PartyTaxScheme
        .cbc_RegistrationName
        .cdata
    )

    parsedXml["emitterId"] = (
        invoice
        .cac_AccountingSupplierParty
        .cac_Party
        .cac_PartyTaxScheme
        .cbc_CompanyID
        .cdata
    )

    parsedXml["payerName"] = (
        invoice
        .cac_AccountingCustomerParty
        .cac_Party
        .cac_PartyTaxScheme
        .cbc_RegistrationName
        .cdata
    )

    parsedXml["payerId"] = (
        invoice
        .cac_AccountingCustomerParty
        .cac_Party
        .cac_PartyTaxScheme
        .cbc_CompanyID
        .cdata
    )

    parsedXml["billValue"] = float(
        invoice.cac_LegalMonetaryTotal.cbc_LineExtensionAmount.cdata
    )

    parsedXml["subTotal"] = parsedXml["billValue"] + parsedXml["iva"]
    parsedXml["total"] = parsedXml["subTotal"]

    parsedXml["dateBill"] = invoice.cbc_IssueDate.cdata

    parsedXml["datePayment"] = get_payment_due_date(invoice)

    parsedXml["cufe"] = invoice.cbc_UUID.cdata

    parsedXml["expirationDate"] = get_expiration_date(invoice)

    return parsedXml


def parseBill(file):
    try:
        xml = untangle.parse(file)

        # ---------------------------------------------------------
        # CASO 1 → El XML viene dentro de AttachedDocument
        # ---------------------------------------------------------
        if hasattr(xml, "AttachedDocument") and hasattr(xml.AttachedDocument, "cac_Attachment"):

            try:
                description = (
                    xml
                    .AttachedDocument
                    .cac_Attachment
                    .cac_ExternalReference
                    .cbc_Description
                    .cdata
                )

                # Corrección importante:
                # esto permite leer XML internos que vienen con espacios/saltos antes de <?xml
                description = clean_embedded_xml(description)

                xml2 = untangle.parse(description)

                if not hasattr(xml2, "Invoice"):
                    return {
                        "error": True,
                        "message": "Invoice no encontrado dentro del AttachedDocument"
                    }

                return parse_invoice(xml2.Invoice)

            except Exception as e:
                logger.exception("Error processing AttachedDocument")
                return {
                    "error": True,
                    "message": f"Error processing AttachedDocument: {str(e)}"
                }

        # ---------------------------------------------------------
        # CASO 2 → El XML viene directamente como Invoice
        # ---------------------------------------------------------
        elif hasattr(xml, "Invoice"):

            try:
                return parse_invoice(xml.Invoice)

            except Exception as e:
                logger.exception("Error processing Invoice")
                return {
                    "error": True,
                    "message": f"Error processing Invoice: {str(e)}"
                }

        # ---------------------------------------------------------
        # SIN AttachedDocument NI Invoice
        # ---------------------------------------------------------
        else:
            return {
                "error": True,
                "message": "AttachedDocument o Invoice no encontrados"
            }

    except Exception as e:
        logger.exception("Error parsing XML")
        return {
            "error": True,
            "message": f"Error parsing XML: {str(e)}"
        }