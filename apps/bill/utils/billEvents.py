import requests
from bs4 import BeautifulSoup
import re
from apps.base.exceptions import HttpException


def billEvents(cufe, update=False):
    try:
        attempts = 0
        page = requests.get(f"https://catalogo-vpfe.dian.gov.co/document/searchqr?documentkey={cufe}")
        while page.text.find('Service unavailable') != -1 and page.text.find('The web server failed to respond within the specified time.') != -1:
            attempts = attempts + 1
            if attempts == 1:
                return {"type": 'a7c70741-8c1a-4485-8ed4-5297e54a978a', "events": [], 'currentOwner': "", 'bill':None}
                break 
            page = requests.get(f"https://catalogo-vpfe.dian.gov.co/document/searchqr?documentkey={cufe}")
        soup = BeautifulSoup(page.content, "html.parser")
        results = soup.find(class_="documents-table table table-striped table-hover align-middle margin-bottom-0")
        getEvents = results.find_all("td", class_="text-center")
        # get the second span with the class cufe-text
        getBillOwner = soup.find_all("span", class_="cufe-text")[1].text
        # get only the after :
        getBillOwnerText = getBillOwner.split(':')[1]
        events = []
        dates  = []
        parsed = []
        valid = False
        regex = re.compile(r"^\d{4}\-(0[1-9]|1[012])\-(0[1-9]|[12][0-9]|3[01])$")

        for event in getEvents:

            if event.text == '030' or event.text == '032' or event.text == '033' or event.text == '036' or event.text == '037' or event.text == '038' or event.text == '046':
                events.append(event.text)

            if re.match(regex, event.text):
                dates.append(event.text)
        for index, x in enumerate(events):
            eventId = ""
            description = ""
            if x == '030':
                valid = True
                eventId = "07c61f28-83f8-4f91-b965-f685f86cf6bf"
                description = "Acuse de recibo de la Factura Electrónica de Venta"
            else:
                valid = False
            if x == '032':
                valid = True
                eventId = "141db270-23ec-49c1-87a7-352d5413d309"
                description = "Recibo del bien o prestación del servicio"
            else:
                valid = False
                
            if x == '033':
                valid = True
                eventId = "c508eeb3-e0e8-48e8-a26f-5295f95c1f1f"
                description = "Aceptación expresa de la Factura Electrónica de Venta" 
            elif x == '034':
                valid = True
                eventId = "e76e9b7a-baeb-4972-b76e-3a8ce2d4fa30"
                description = "Aceptación tácita de la Factura Electrónica de Venta"
            else:
                valid = False
                
                
            if update == True:
                if x == '036':
                    valid = True
                    eventId = "b8d4f8d3-aded-4b1f-873e-46c89a2538ed"
                    description = "Primera inscripción de la Factura Electrónica de Venta como Título Valor en el RADIAN para negociación general"
    
                if x == '037':
                    valid = True
                    eventId = "3ea77762-7208-457a-b035-70069ee42b5e"
                    description = "Endoso electrónico en propiedad con responsabilidad"
    
                if x == '038':
                    valid = True
                    eventId = '0e333b6b-27b1-4aaf-87ce-ad60af6e52e6'
                    description = "Endoso en garantía"
                
                if x == '046':
                    valid=True
                    eventId = "f5d475c0-4433-422f-b3d2-7964ea0aa5c4"
                    description = "Informe para el pago de la Factura Electrónica de Venta como Título Valor"
            parsed.append({'event': eventId, 'description': description, 'date': dates[index]})

        # delete the objects with the event ""
        parsed = [x for x in parsed if x['event'] != ""]
        return {"type": 'a7c70741-8c1a-4485-8ed4-5297e54a978a',
                "events": parsed, 'currentOwner': getBillOwnerText, 'bill':page.content} if valid else {"type": 'fdb5feb4-24e9-41fc-9689-31aff60b76c9', "events": parsed,
                                                                                   'currentOwner': getBillOwnerText, 'bill':page.content}
    except Exception as e:
        raise(e)
