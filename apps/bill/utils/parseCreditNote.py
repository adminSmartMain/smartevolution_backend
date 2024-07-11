import xmltodict

def parseCreditNote(file):
    xml = {}
    data = xmltodict.parse(file)
    if 'CreditNote' in data:
        creditNote = data['CreditNote']
    else:
        creditNote = data['AttachedDocument']['cac:Attachment']['cac:ExternalReference']['cbc:Description']

    parseCreditNote = xmltodict.parse(creditNote)

    xml['creditNoteId'] = parseCreditNote['CreditNote']['cbc:ID']
    xml['associatedInvoice'] = parseCreditNote['CreditNote']['cac:BillingReference']['cac:InvoiceDocumentReference']['cbc:ID']
    xml['total'] = float(parseCreditNote['CreditNote']['cac:LegalMonetaryTotal']['cbc:PayableAmount']['#text'])
    return xml
