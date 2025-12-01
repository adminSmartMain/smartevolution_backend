import requests
from apps.base.exceptions import HttpException
from datetime import datetime

def updateBillEvents(bill_data):
    try:
        if bill_data is None:
            return []

        events_from_api = bill_data.get('data', {}).get('attributes', {}).get('events', [])

        # Solo eventos que se actualizan
        event_code_to_uuid = {
            '036': 'b8d4f8d3-aded-4b1f-873e-46c89a2538ed',
            '037': '3ea77762-7208-457a-b035-70069ee42b5e',
            '038': '0e333b6b-27b1-4aaf-87ce-ad60af6e52e6',
            '046': 'f5d475c0-4433-422f-b3d2-7964ea0aa5c4'
        }

        parsed_events = []

        for ev in events_from_api:
            code = ev.get("code")

            if code in event_code_to_uuid:
                uuid = event_code_to_uuid[code]
                date = ""

                details = ev.get("details", [])
                if details and "timestamp" in details[0]:
                    ts = details[0]["timestamp"]
                    date = datetime.fromtimestamp(ts / 1000).strftime('%Y-%m-%d')

                parsed_events.append({
                    "event": uuid,
                    "date": date,
                    "code": code
                })

        return parsed_events

    except Exception as e:
        print(f"Error en updateBillEvents: {str(e)}")
        return []
