# apps/bill/utils/events.py  (o donde tengas ts_to_datetime / normalize_description)
import re
from datetime import datetime
from zoneinfo import ZoneInfo

def normalize_description(text: str) -> str:
    if not text:
        return ""
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text

BOGOTA_TZ = ZoneInfo("America/Bogota")

def ts_to_datetime(ts_ms: int):
    """
    Convierte timestamp (ms) a datetime naive en hora Colombia.
    ✅ Importante: microsecond=0 para deduplicación estable.
    """
    if ts_ms is None:
        return None

    aware = datetime.fromtimestamp(int(ts_ms) / 1000, tz=BOGOTA_TZ)
    naive = aware.replace(tzinfo=None)
    return naive.replace(microsecond=0)