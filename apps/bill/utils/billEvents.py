import requests
from apps.base.exceptions import HttpException
import environ
import logging

from .events import normalize_description, ts_to_datetime  # ajusta el import a donde lo pongas

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

env = environ.Env()

UUID_FV = "fdb5feb4-24e9-41fc-9689-31aff60b76c9"
UUID_FV_TV = "a7c70741-8c1a-4485-8ed4-5297e54a978a"
UUID_RECHAZADA = "dcec6f03-5dc1-42ea-a525-afada28686da"
UUID_ENDOSADA = "29113618-6ab8-4633-aa8e-b3d6f242e8a4"


def billEvents(cufe, update=False):
    """
    Devuelve:
      - ok=True  -> Billy respondió bien (200) y devolvemos eventos
      - ok=False -> Timeout/network/no-200 (y NO debemos actualizar nada en DB)

    warning: texto corto para mostrar en frontend si aplica.
    """
    try:
        token = env('SMART_TOKEN')

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        logger.debug(f'Fetching bill events for CUFE: {cufe}')

        try:
            resp = requests.get(
                f"https://api.billy.com.co/v2/invoices?cufe={cufe}",
                headers=headers,
                timeout=5
            )

            if resp.status_code == 200:
                bill_data = resp.json()
                attributes = bill_data.get("data", {}).get("attributes", {})

                events_api = attributes.get("events", [])
                current_owner = attributes.get("holderName", "") or ""
                current_ownerId = attributes.get("holderIdNumber", "") or ""

                codes = set(ev.get("code", "") for ev in events_api)

                is_reject = "031" in codes
                is_endosada = any(c in codes for c in ["037", "047", "046"])
                is_fv_tv = ("030" in codes and "032" in codes and ("033" in codes or "034" in codes))

                parsed_events = []

                for ev in events_api:
                    code = ev.get("code", "") or ""

                    # Filtrar por update (tu regla original)
                    if code in ['036', '037', '038', '046'] and not update:
                        continue

                    details = ev.get("details", []) or []
                    if not details:
                        continue

                    for d in details:
                        desc = d.get("description", "") or ""
                        date = ts_to_datetime(d.get("timestamp"))

                        parsed_events.append({
                            "code": code,
                            "description": desc,
                            "description_norm": normalize_description(desc),
                            "date": date,
                            # si más adelante quieres DIAN:
                            # "dianDescription": d.get("dianDescription", "") o lo que corresponda
                        })

                if is_reject:
                    response_type = UUID_RECHAZADA
                elif is_endosada:
                    response_type = UUID_ENDOSADA
                elif is_fv_tv:
                    response_type = UUID_FV_TV
                else:
                    response_type = UUID_FV

                return {
                    "ok": True,
                    "type": response_type,
                    "events": parsed_events,
                    "currentOwner": current_owner,
                    "current_ownerId": current_ownerId,
                    "bill": bill_data,
                    "warning": None
                }

            # ❌ NO 200: no tocar DB
            logger.warning(f'Billy API returned status {resp.status_code} for CUFE: {cufe}')
            return {
                "ok": False,
                "error": "billy_non_200",
                "status_code": resp.status_code,
                "warning": "Billy no respondió correctamente (status != 200).",
                "type": None,
                "events": None,
                "currentOwner": None,
                "current_ownerId": None,
                "bill": None
            }

        except requests.exceptions.Timeout:
            logger.warning(f'Timeout (3s) fetching bill events for CUFE: {cufe}')
            return {
                "ok": False,
                "error": "billy_timeout",
                "warning": "Billy está lento (timeout). Los eventos no se pudieron actualizar.",
                "type": None,
                "events": None,
                "currentOwner": None,
                "current_ownerId": None,
                "bill": None
            }

        except requests.exceptions.RequestException as req_err:
            logger.error(f'Network error for CUFE {cufe}: {str(req_err)}')
            return {
                "ok": False,
                "error": "billy_network_error",
                "warning": "Error de red consultando Billy. Los eventos no se pudieron actualizar.",
                "type": None,
                "events": None,
                "currentOwner": None,
                "current_ownerId": None,
                "bill": None
            }

    except Exception as e:
        logger.error(f'Unexpected error for CUFE {cufe}: {str(e)}')
        raise HttpException(str(e))