import re
from datetime import datetime
from typing import Any, Dict, List

def normalize_timestamp(value: Any) -> datetime | None:
    """Try to parse various timestamp formats into datetime."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except Exception:
        return None

def mask_pii(text: str) -> str:
    """Very basic PII masking (emails, phone numbers)."""
    if not text:
        return text
    text = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[EMAIL]", text)
    text = re.sub(r"\b\d{10,}\b", "[PHONE]", text)
    return text

def dedupe_records(records: List[Dict[str, Any]], key: str = "external_id") -> List[Dict[str, Any]]:
    """Deduplicate based on external_id (or another key)."""
    seen, deduped = set(), []
    for rec in records:
        val = rec.get(key)
        if val and val in seen:
            continue
        if val:
            seen.add(val)
        deduped.append(rec)
    return deduped

def clean_feedback_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Apply normalization & PII masking to raw feedback records."""
    cleaned = []
    for rec in records:
        rec["raw_text"] = mask_pii(rec.get("raw_text", ""))
        rec["created_at"] = normalize_timestamp(rec.get("created_at"))
        cleaned.append(rec)
    return dedupe_records(cleaned)
