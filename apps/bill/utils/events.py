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
    if ts_ms is None:
        return None

    aware = datetime.fromtimestamp(int(ts_ms) / 1000, tz=BOGOTA_TZ)
    return aware.replace(tzinfo=None)  # <-- naive, pero ya en hora Colombia