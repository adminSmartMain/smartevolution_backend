import requests
from apps.base.exceptions import HttpException
import environ
import logging
from datetime import datetime

from .events import normalize_description, ts_to_datetime_str # ajusta el import a donde lo pongas

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

env = environ.Env()


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
            response = requests.get(
                f"https://api.billy.com.co/v2/invoices?cufe={cufe}",
                headers=headers,
                timeout=3
            )

            if response.status_code == 200:
                bill_data = response.json()
                attributes = bill_data.get("data", {}).get("attributes", {})

                events_api = attributes.get("events", [])
                current_owner = attributes.get("holderName", "")
                current_ownerId = attributes.get("holderIdNumber", "")

                # FLAGS (igual que antes)
                codes = set(ev.get("code", "") for ev in events_api)

                is_reject = "031" in codes
                is_endosada = any(c in codes for c in ["037", "047", "046"])
                is_fv_tv = ("030" in codes and "032" in codes and ("033" in codes or "034" in codes))

                # Aplanar eventos:
                # - si ev trae details (lista), cada detail => un evento individual
                parsed_events = []

                for ev in events_api:
                    code = ev.get("code", "")

                    # Filtrar por update (tu regla original)
                    if code in ['036', '037', '038', '046'] and not update:
                        continue

                    details = ev.get("details", []) or []

                    # si no trae details, igual generamos 1 evento “vacío”
                    if not details:
                        continue


                    for d in details:
                        desc = d.get("description", "") or ""

                        date = ts_to_datetime_str(d.get("timestamp"))

                        parsed_events.append({
                            "code": code,
                            "description": desc,
                            "description_norm": normalize_description(desc),
                            "date": date
                        })

                # Tipo final (igual que antes)
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
                    "events": parsed_events,              # ✅ ahora eventos por code+detail
                    "currentOwner": current_owner,
                    "current_ownerId": current_ownerId,
                    "bill": bill_data
                }

            logger.warning(f'API returned status {response.status_code} for CUFE: {cufe}')
            return {
                "type": UUID_FV,
                "events": [],
                "currentOwner": "No disponible",
                "current_ownerId": "",
                "bill": None
            }

        except requests.exceptions.Timeout:
            logger.warning(f'Timeout (3s) fetching bill events for CUFE: {cufe}')
            return {
                "type": UUID_FV,
                "events": [],
                "currentOwner": "No disponible",
                "current_ownerId": "",
                "bill": []
            }

        
        except requests.exceptions.RequestException as req_err:
            logger.error(f'Network error for CUFE {cufe}: {str(req_err)}')
            return {
                "type": UUID_FV,
                "events": [],
                "currentOwner": "No disponible",
                "current_ownerId": "",
                "bill": []
            }

    except Exception as e:
        logger.error(f'Unexpected error for CUFE {cufe}: {str(e)}')
        raise HttpException(str(e))
