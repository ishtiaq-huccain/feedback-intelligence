from typing import Optional

from sqlalchemy import (
    Column, Integer, String, DateTime, Text, JSON, Boolean, Float,
    ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from backend.database.database import Base
from backend.config import get_settings
from datetime import datetime, timezone
settings = get_settings()

# pgvector fallback to keep code importable if extension/client isn't present
try:
    from pgvector.sqlalchemy import Vector
    VECTOR_TYPE = Vector
except Exception:
    # NOTE: similarity queries won't work with this fallback
    class _VectorFallback(String):  # type: ignore
        pass
    VECTOR_TYPE = _VectorFallback  # type: ignore


class IngestionRun(Base):
    """
    One ingestion process (CSV/JSON upload or API fetch).
    Tracks counts and row-level errors for audit/debugging.
    """
    __tablename__ = "ingestion_runs"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False)  # csv, json, api
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)

    total_rows = Column(Integer, default=0)
    ingested_rows = Column(Integer, default=0)
    rejected_rows = Column(Integer, default=0)
    errors = Column(JSONB, default=list)  # [{row, reason}, ...]

    # Relationship
    feedback_items = relationship("Feedback", back_populates="run", lazy="joined")


class Feedback(Base):
    """
    Individual feedback (review, ticket, NPS).
    Stores raw text, optional payload, model labels, analyst overrides, and embedding.
    """
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True)

    # Source references
    external_id = Column(String(128), index=True)   # e.g., review/ticket id from source system
    source = Column(String(50), index=True)         # "review", "ticket", "nps"
    batch_id = Column(Integer, ForeignKey("ingestion_runs.id", ondelete="SET NULL"))

    # Optional metadata
    user_id = Column(String(128))
    locale = Column(String(16))
    product = Column(String(64))
    version = Column(String(32))

    created_at = Column(DateTime, index=True)       # when the user wrote it
    received_at = Column(DateTime, default=datetime.utcnow)  # when we ingested it

    # Raw
    raw_text = Column(Text, nullable=False)
    raw_payload = Column(JSONB)  # unstructured original record

    # Model-generated labels
    sentiment = Column(String(16))       # "positive" | "neutral" | "negative"
    sentiment_conf = Column(Float)
    category = Column(String(64))
    category_conf = Column(Float)
    aspects = Column(JSONB)              # e.g., [{"aspect": "performance", "conf": 0.82}, ...]
    priority = Column(String(16))        # "low" | "medium" | "high"

    # Analyst overrides
    override_labels = Column(Boolean, default=False)
    corrected_sentiment = Column(String(16))
    corrected_category = Column(String(64))
    corrected_aspects = Column(JSONB)

    # Embedding
    embedding = Column(VECTOR_TYPE(384)) if settings.use_pgvector else Column(Text)

    # Relationship
    run = relationship("IngestionRun", back_populates="feedback_items", lazy="joined")

    __table_args__ = (
        Index("ix_feedback_created_product", "created_at", "product"),
        Index("ix_feedback_category", "category"),
        Index("ix_feedback_sentiment", "sentiment"),
    )


class KBDoc(Base):
    """
    Knowledge base document (FAQ, release notes, specs).
    Raw text stored here; chunking/indexing is downstream.
    """
    __tablename__ = "kb_docs"

    id = Column(Integer, primary_key=True)
    title = Column(String(256), nullable=False)
    source = Column(String(50), nullable=False)   # "upload", "url"
    content_type = Column(String(32))             # "txt", "md", "pdf"
    path = Column(String(512))                    # stored location if file-based

    raw_text = Column(Text)                       # original content
    doc_metadata = Column(JSONB)                  # arbitrary metadata

    embedding = Column(VECTOR_TYPE(384)) if settings.use_pgvector else Column(Text)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    chunks = relationship("KBChunk", back_populates="doc", cascade="all, delete-orphan")


    __table_args__ = (
        Index("ix_kb_title", "title"),
    )
class KBChunk(Base):
    """
    Chunks of a KB doc with embeddings.
    """
    __tablename__ = "kb_chunks"

    id = Column(Integer, primary_key=True)
    doc_id = Column(Integer, ForeignKey("kb_docs.id", ondelete="CASCADE"))
    chunk_index = Column(Integer)
    text = Column(Text)
    embedding = Column(VECTOR_TYPE(384)) if settings.use_pgvector else Column(Text)

    doc = relationship("KBDoc", back_populates="chunks")

    __table_args__ = (Index("ix_kb_chunk_doc", "doc_id"),)

class SearchIndex(Base):
    """
    Unified semantic index across feedback, KB chunks, FAQs, notes.
    Allows RAG to search across all knowledge sources.
    """
    __tablename__ = "search_index"

    id = Column(Integer, primary_key=True)
    ref_type = Column(String(24), nullable=False)      # "feedback" | "kb_chunk" | "faq" | "note"
    ref_id = Column(Integer, nullable=False)           # ID in the source table (or synthetic for faq/note)
    title = Column(String(256))                        # Optional title
    text = Column(Text, nullable=False)                # The chunk text
    meta_data = Column("metadata", JSON)             # e.g. {"product": "iPhone", "locale": "en"}

    # Embedding (bge-small-en-v1.5 → 384 dim)
    embedding = Column(VECTOR_TYPE(384)) if settings.use_pgvector else Column(Text)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_search_ref", "ref_type", "ref_id"),
        Index("ix_search_created", "created_at"),
    )

