import re
from datetime import datetime, timezone

def normalize_description(text: str) -> str:
    """
    Normaliza para comparar descripciones:
    - strip
    - colapsa espacios
    - lower
    """
    if not text:
        return ""
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text

def ts_to_datetime_str(ts_ms: int, tz=timezone.utc) -> str:
    if ts_ms is None:
        return None
    dt = datetime.fromtimestamp(int(ts_ms) / 1000, tz=tz)
    return dt.strftime("%Y-%m-%d %H:%M:%S")