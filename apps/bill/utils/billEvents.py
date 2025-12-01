import requests
from apps.base.exceptions import HttpException
import environ
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

env = environ.Env()

# UUIDs finales
UUID_FV = "fdb5feb4-24e9-41fc-9689-31aff60b76c9"
UUID_FV_TV = "a7c70741-8c1a-4485-8ed4-5297e54a978a"
UUID_RECHAZADA = "dcec6f03-5dc1-42ea-a525-afada28686da"
UUID_ENDOSADA = "29113618-6ab8-4633-aa8e-b3d6f242e8a4"

def billEvents(cufe, update=False):
    try:
        token = env('SMART_TOKEN')

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        logger.debug(f'Fetching bill events for CUFE: {cufe}')

        response = requests.get(
            f"https://api.billy.com.co/v2/invoices?cufe={cufe}",
            headers=headers
        )

        if response.status_code != 200:
            return {
                "type": UUID_FV,
                "events": [],
                "currentOwner": "",
                "bill": None
            }

        bill_data = response.json()
        attributes = bill_data.get("data", {}).get("attributes", {})

        events_api = attributes.get("events", [])
        current_owner = attributes.get("holderName", "")

        # Mapeo general
        event_code_to_uuid = {
            '030': '07c61f28-83f8-4f91-b965-f685f86cf6bf',
            '031': '3d376019-618b-40eb-ae80-9cb143db54a4',
            '032': '141db270-23ec-49c1-87a7-352d5413d309',
            '033': 'c508eeb3-e0e8-48e8-a26f-5297f95c1f1f',
            '034': 'e76e9b7a-baeb-4972-b76e-3a8ce2d4fa30',
            '036': 'b8d4f8d3-aded-4b1f-873e-46c89a2538ed',
            '037': '3ea77762-7208-457a-b035-70069ee42b5e',
            '038': '0e333b6b-27b1-4aaf-87ce-ad60af6e52e6',
            '046': 'f5d475c0-4433-422f-b3d2-7964ea0aa5c4'
        }

        parsed_events = []

        # Flags de estado
        is_fv_tv = False
        is_reject = False
        is_endosada = False

        for ev in events_api:
            code = ev.get("code", "")

            # --- FLAGS ---
            if code in ["030", "032", "033", "034"]:
                is_fv_tv = True

            if code == "031":
                is_reject = True

            if code in ["037", "046", "047"]:
                is_endosada = True

            # --- FILTRAR POR update ---
            if code in ['036', '037', '038', '046'] and not update:
                continue

            # --- MAPEO DE EVENTO ---
            if code in event_code_to_uuid:
                details = ev.get("details", [])
                date = ""

                if details and "timestamp" in details[0]:
                    ts = details[0]["timestamp"]
                    date = datetime.fromtimestamp(ts / 1000).strftime('%Y-%m-%d')

                parsed_events.append({
                    "event": event_code_to_uuid[code],
                    "date": date,
                    "description": details[0].get("description", "") if details else ""
                })

        # === DETERMINAR TIPO ===
        if is_reject:
            response_type = UUID_RECHAZADA
        elif is_endosada:
            response_type = UUID_ENDOSADA
        elif is_fv_tv:
            response_type = UUID_FV_TV
        else:
            response_type = UUID_FV

        return {
            "type": response_type,
            "events": parsed_events,
            "currentOwner": current_owner,
            "bill": bill_data
        }

    except Exception as e:
        raise HttpException(str(e))
