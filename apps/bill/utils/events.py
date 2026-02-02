import re
from datetime import datetime

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

def ts_to_date_str(ts_ms):
    """
    Convierte timestamp en ms a 'YYYY-MM-DD'. Si no puede, retorna ''.
    """
    try:
        ts_ms = int(ts_ms)
        return datetime.fromtimestamp(ts_ms / 1000).strftime("%Y-%m-%d")
    except Exception:
        return ""
