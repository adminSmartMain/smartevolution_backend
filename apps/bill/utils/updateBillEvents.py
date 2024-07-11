import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import re
from apps.base.exceptions import HttpException



def billEvents(bill):
    try:
        if bill == None:
            return None
        soup = BeautifulSoup(bill, "html.parser")
        results = soup.find(
            class_="documents-table table table-striped table-hover align-middle margin-bottom-0")
        getEvents = results.find_all("td", class_="text-center")
        events = []
        dates  = []
        parsed = []
        regex = re.compile(
            r"^\d{4}\-(0[1-9]|1[012])\-(0[1-9]|[12][0-9]|3[01])$")

        for event in getEvents:
            if event.text == '036' or event.text == '037' or event.text == '038' or event.text == '046':
                events.append(event.text)

            if re.match(regex, event.text):
                dates.append(event.text)

        for index, x in enumerate(events):
            eventId = ""
            if x == '036':
                eventId = "b8d4f8d3-aded-4b1f-873e-46c89a2538ed"
            if x == '037':
                eventId = "3ea77762-7208-457a-b035-70069ee42b5e"
            if x == '038':
                eventId = '0e333b6b-27b1-4aaf-87ce-ad60af6e52e6'
            if x == '046':
                eventId = "f5d475c0-4433-422f-b3d2-7964ea0aa5c4"

            parsed.append(
                {'event': eventId, 'date': dates[index], 'code':x})
        return parsed

    except Exception as e:
        pass