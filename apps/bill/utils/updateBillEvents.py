from datetime import datetime
from .events import normalize_description, ts_to_datetime  # ajusta el import

def updateBillEvents(bill_data):
    try:
        if bill_data is None:
            return []

        events_from_api = bill_data.get('data', {}).get('attributes', {}).get('events', [])

        parsed_events = []

        for ev in events_from_api:
            code = ev.get("code", "")
            details = ev.get("details", []) or []

            if not details:
                parsed_events.append({
                    "code": code,
                    "description": "",
                    "description_norm": "",
                    "date": ""
                })
                continue

            for d in details:
                desc = d.get("description", "") or ""
                date = ts_to_datetime(d.get("timestamp"))

                parsed_events.append({
                    "code": code,
                    "description": desc,
                    "description_norm": normalize_description(desc),
                    "date": date
                })

        return parsed_events

    except Exception as e:
        print(f"Error en updateBillEvents: {str(e)}")
        return []
