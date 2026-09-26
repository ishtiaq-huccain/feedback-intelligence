import logging
from sqlalchemy.orm import Session
from backend.database.models import Feedback, KBChunk, SearchIndex
from backend.ml.embedding_service import EmbeddingService  # wrapper for bge-small-en-v1.5

logger = logging.getLogger(__name__)


class IndexerService:
    def __init__(self, db: Session):
        self.db = db
        self.embedder = EmbeddingService(db)

    def index_feedback(self, limit: int = 1000):
        """
        Index feedback entries into the unified search index.
        """
        feedback_items = (
            self.db.query(Feedback)
            .filter(Feedback.embedding.isnot(None))
            .limit(limit)
            .all()
        )

        indexed = 0
        for fb in feedback_items:
            exists = (
                self.db.query(SearchIndex)
                .filter_by(ref_type="feedback", ref_id=fb.id)
                .first()
            )
            if exists:
                continue  # skip already indexed

            entry = SearchIndex(
                ref_type="feedback",
                ref_id=fb.id,
                title=f"Feedback {fb.id}",
                text=fb.raw_text,
                metadata={
                    "product": fb.product,
                    "locale": fb.locale,
                    "version": fb.version,
                    "sentiment": fb.sentiment,
                    "category": fb.category,
                },
                embedding=fb.embedding,  # reuse existing
            )
            self.db.add(entry)
            indexed += 1

        self.db.commit()
        logger.info(f"Indexed {indexed} feedback entries.")
        return indexed

    def index_kb_chunks(self, limit: int = 1000):
        """
        Index KB chunks into the unified search index.
        """
        chunks = (
            self.db.query(KBChunk)
            .filter(KBChunk.embedding.isnot(None))
            .limit(limit)
            .all()
        )

        indexed = 0
        for chunk in chunks:
            exists = (
                self.db.query(SearchIndex)
                .filter_by(ref_type="kb_chunk", ref_id=chunk.id)
                .first()
            )
            if exists:
                continue

            entry = SearchIndex(
                ref_type="kb_chunk",
                ref_id=chunk.id,
                title=f"KB Doc {chunk.doc_id} - Chunk {chunk.chunk_index}",
                text=chunk.text,
                metadata={"doc_id": chunk.doc_id},
                embedding=chunk.embedding,
            )
            self.db.add(entry)
            indexed += 1

        self.db.commit()
        logger.info(f"Indexed {indexed} KB chunks.")
        return indexed
