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

        try:
            # Intentar la petición con timeout de 3 segundos
            response = requests.get(
                f"https://api.billy.com.co/v2/invoices?cufe={cufe}",
                headers=headers,
                timeout=3  # Timeout de 3 segundos
            )
            
            # Si llegamos aquí, la petición no tuvo timeout
            if response.status_code == 200:
                bill_data = response.json()
                attributes = bill_data.get("data", {}).get("attributes", {})

                events_api = attributes.get("events", [])
                current_owner = attributes.get("holderName", "")
                current_ownerId = attributes.get("holderIdNumber", "")
                # Mapeo general
                event_code_to_uuid = {
                    '030': '07c61f28-83f8-4f91-b965-f685f86cf6bf',
                    '031': '3d376019-618b-40eb-ae80-9cb143db54a4',
                    '032': '141db270-23ec-49c1-87a7-352d5413d309',
                    '033': 'c508eeb3-e0e8-48e8-a26f-5297f95c1f1',
                    '034': 'e76e9b7a-baeb-4972-b76e-3a8ce2d4fa30',
                    '036': 'b8d4f8d3-aded-4b1f-873e-46c89a2538ed',
                    '037': '3ea77762-7208-457a-b035-70069ee42b5e',
                    '038': '0e333b6b-27b1-4aaf-87ce-ad60af6e52e6',
                    '046': 'f5d475c0-4433-422f-b3d2-7964ea0aa5c4',
                    '047': '3bb86c74-1d1c-4986-a905-a47624b09322',
                }

                parsed_events = []

                # === FLAGS CORREGIDOS SEGÚN LA REGLA FINAL ===
                codes = set(ev.get("code", "") for ev in events_api)

                is_reject = "031" in codes
                is_endosada = any(c in codes for c in ["037", "047", "046"])
                is_fv_tv = ("030" in codes and "032" in codes and ("033" in codes or "034" in codes))

                for ev in events_api:
                    code = ev.get("code", "")

                    # Filtrar por update
                    if code in ['036', '037', '038', '046'] and not update:
                        continue

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

                # === LÓGICA FINAL: ORDEN JERÁRQUICO ===
                if is_reject:
                    response_type = UUID_RECHAZADA
                elif is_endosada:
                    # ✔ FV-TV + Endoso = ENDOSADA
                    response_type = UUID_ENDOSADA
                elif is_fv_tv:
                    response_type = UUID_FV_TV
                else:
                    response_type = UUID_FV

                return {
                    "type": response_type,
                    "events": parsed_events,
                    "currentOwner": current_owner,
                    "current_ownerId": current_ownerId,
                    "bill": bill_data
                }
            
            else:
                # La API respondió con un código de error (409, 400, 404, 500, etc.)
                # Pero NO es un timeout
                logger.warning(f'API returned status {response.status_code} for CUFE: {cufe}')
                return {
                    "type": UUID_FV,
                    "events": [],
                    "currentOwner": "",
                    "bill": None
                }
                
        except requests.exceptions.Timeout:
            # TIMEOUT después de 3 segundos
            logger.warning(f'Timeout (3s) fetching bill events for CUFE: {cufe}')
            return {
                "type": UUID_FV,
                "events": [],
                "currentOwner": "No disponible",
                "bill": []
            }
            
        except requests.exceptions.RequestException as req_err:
            # Otros errores de red (conexión rechazada, DNS, etc.)
            logger.error(f'Network error for CUFE {cufe}: {str(req_err)}')
            return {
                "type": UUID_FV,
                "events": [],
                "currentOwner": "No disponible",
                "bill": []
            }

    except Exception as e:
        logger.error(f'Unexpected error for CUFE {cufe}: {str(e)}')
        raise HttpException(str(e))