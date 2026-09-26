from typing import Any, Dict, List, Tuple
from sqlalchemy.orm import Session
from backend.database import models
from backend.utils.data_cleaner import clean_feedback_records
from datetime import datetime
from datetime import datetime

def serialize_payload(record: dict) -> dict:
    """
    Convert datetime objects in record to ISO strings for JSONB storage.
    """
    clean = {}
    for k, v in record.items():
        if isinstance(v, datetime):
            clean[k] = v.isoformat()
        else:
            clean[k] = v
    return clean


def ingest_feedback(db: Session, source: str, records: List[Dict[str, Any]]) -> models.IngestionRun:
    """
    Ingest feedback items into DB.
    Returns the created IngestionRun object (with counts).
    """
    run = models.IngestionRun(source=source, started_at=datetime.utcnow())
    db.add(run)
    db.commit()
    db.refresh(run)

    cleaned = clean_feedback_records(records)

    ingested, rejected, errors = 0, 0, []
    for i, rec in enumerate(cleaned, start=1):
        try:
            fb = models.Feedback(
                external_id=rec.get("external_id"),
                source=rec.get("source", source),
                batch_id=run.id,
                user_id=rec.get("user_id"),
                locale=rec.get("locale"),
                product=rec.get("product"),
                version=rec.get("version"),
                created_at=rec.get("created_at"),
                raw_text=rec.get("raw_text"),
                raw_payload=serialize_payload(rec),  # 👈 make JSONB safe
            )
            db.add(fb)
            ingested += 1
        except Exception as e:
            rejected += 1
            errors.append({"row": i, "reason": str(e)})

    run.total_rows = len(records)
    run.ingested_rows = ingested
    run.rejected_rows = rejected
    run.errors = errors
    run.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(run)
    return run

