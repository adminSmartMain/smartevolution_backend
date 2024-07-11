from apps.bill.models import Bill
import requests
from bs4 import BeautifulSoup
import re
from apps.base.utils.index import sendEmail

def check_bills_by_cufe():
    try:
        sendEmail('facturas - smart evolution', "inicio cronjob", "ander.er985@gmail.com")
        bills = Bill.objects.all()
        counter = 0
        for bill in bills:
            if bill.cufe == None:
                pass
            else:
                page = requests.get(f"https://catalogo-vpfe.dian.gov.co/document/searchqr?documentkey={bill.cufe}")
            while page.text.find('Service unavailable') != -1:
                page = requests.get(f"https://catalogo-vpfe.dian.gov.co/document/searchqr?documentkey={bill.cufe}")
            soup = BeautifulSoup(page.content, "html.parser")
            results = soup.find(class_="documents-table table table-striped table-hover align-middle margin-bottom-0")
            getEvents = results.find_all("td", class_="text-center")
            # get the second span with the class cufe-text
            getBillOwner = soup.find_all("span", class_="cufe-text")[1].text
            # get only the after :
            getBillOwnerText = getBillOwner.split(':')[1]
            events = []
            dates  = []
            valid = False
            regex = re.compile(r"^\d{4}\-(0[1-9]|1[012])\-(0[1-9]|[12][0-9]|3[01])$")
            for event in getEvents:
                if event.text == '036' or event.text == '037' or event.text == '038' or event.text == '046':
                    events.append(event.text)
                if re.match(regex, event.text):
                    dates.append(event.text)
            for index, x in enumerate(events):
                if x == '036':
                    valid = True
                if x == '037':
                    valid = True
                if x == '038':
                    valid = True
                if x == '046':
                    valid = True
            if valid == True:
                bill.endorsed = True
                parseCurrentOwner = getBillOwnerText.strip()
                bill.currentOwner = parseCurrentOwner
                bill.save()
                #if the current owner have parts of the emitter name then is the same but if not is different check
                keywords = parseCurrentOwner.split(' ')
                excludeWords = ['S.A.S', 'S.A', 'LTDA', 'LTDA.', 'SAS', 'P.A']
                # delete the exclude words from the keywords
                for excludeWord in excludeWords:
                    if excludeWord in keywords:
                        keywords.remove(excludeWord)
                for word in keywords:
                    if word.lower() in bill.emitterName.lower():
                        bill.sameCurrentOwner = True
                        bill.save()
                        break
                counter += 1
            else:
                parseCurrentOwner = getBillOwnerText.strip()
                bill.currentOwner = parseCurrentOwner
                bill.save()
                #if the current owner have parts of the emitter name then is the same but if not is different check
                keywords = parseCurrentOwner.split(' ')
                excludeWords = ['S.A.S', 'S.A', 'LTDA', 'LTDA.', 'SAS', 'P.A']
                for excludeWord in excludeWords:
                    if excludeWord in keywords:
                        keywords.remove(excludeWord)
                for word in keywords:
                    if word.lower() in bill.emitterName.lower():
                        bill.sameCurrentOwner = True
                        bill.save()
                        break
                counter += 1


        sendEmail('facturas - smart evolution', f"facturas actualizadas {counter}", "ander.er985@gmail.com")
    except Exception as e:
        sendEmail('facturas - smart evolution', str(e), "ander.er985@gmail.com")
        pass
