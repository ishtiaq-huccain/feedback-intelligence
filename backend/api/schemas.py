from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


# ---- Feedback ----
class AspectItem(BaseModel):
    aspect: str
    conf: float | None = None

class FeedbackCreate(BaseModel):
    text: str = Field(..., alias="text")
    external_id: str | None = None
    source: str | None = None
    user_id: str | None = None
    locale: str | None = None
    product: str | None = None
    version: str | None = None
    created_at: str | None = None   # ISO datetime string
    raw_payload: Dict[str, Any] | None = None

class FeedbackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    raw_text: str
    sentiment: str | None = None
    category: str | None = None
    aspects: List[AspectItem] | None = None
    priority: str | None = None
    override_labels: bool | None = None


# ---- KBDoc ----
class KBDocCreate(BaseModel):
    title: str
    source: str = "upload"
    content_type: str | None = None
    raw_text: str
    doc_metadata: Dict[str, Any] | None = None

class KBDocRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    source: str
    content_type: str | None = None


# ---- IngestionRun ----
class IngestionRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    total_rows: int
    ingested_rows: int
    rejected_rows: int
