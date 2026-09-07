from dataclasses import dataclass, field
from typing import Any


@dataclass
class NormalizedBillyEvent:
    code: str
    details: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class NormalizedBillyInvoice:
    cufe: str
    status: str
    current_owner: str
    current_owner_id: str
    events_last_update: str | None
    events: list[NormalizedBillyEvent]
    raw: dict[str, Any]


class BillyInvoiceNormalizer:
    @staticmethod
    def normalize(payload: dict[str, Any]) -> NormalizedBillyInvoice:
        attributes = payload.get("data", {}).get("attributes", {}) or {}

        raw_events = attributes.get("events", []) or []

        events = [
            NormalizedBillyEvent(
                code=(event.get("code", "") or "").strip(),
                details=event.get("details", []) or [],
            )
            for event in raw_events
        ]

        return NormalizedBillyInvoice(
            cufe=attributes.get("cufe", "") or "",
            status=attributes.get("status", "") or "",
            current_owner=attributes.get("holderName", "") or "",
            current_owner_id=attributes.get("holderIdNumber", "") or "",
            events_last_update=attributes.get("eventsLastUpdate"),
            events=events,
            raw=payload,
        )