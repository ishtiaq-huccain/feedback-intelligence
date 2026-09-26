from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from backend.database.models import Feedback

class EmbeddingService:
    def __init__(self, db: Session):
        self.db = db
        # Load bge-small-en-v1.5
        self.model = SentenceTransformer("BAAI/bge-small-en-v1.5")

    def embed_text(self, text: str):
        """Return embedding vector for a given text."""
        return self.model.encode(text, normalize_embeddings=True).tolist()

    def embed(self, text: str):
        """
        Alias for embed_text (for consistency with KB ingestion).
        """
        return self.embed_text(text)

    def generate_embeddings_batch(self, limit: int = 50):
        """
        Generate embeddings for feedback rows that are missing embeddings.
        """
        rows = (
            self.db.query(Feedback)
            .filter(Feedback.embedding.is_(None))
            .limit(limit)
            .all()
        )

        results = []
        for row in rows:
            if row.raw_text:
                row.embedding = self.embed_text(row.raw_text)
                results.append({
                    "id": row.id,
                    "text": row.raw_text[:50],
                    "embedded": True
                })

        self.db.commit()
        return results

    def generate_all_embeddings(self):
        """
        Generate embeddings for ALL rows without embeddings.
        """
        rows = (
            self.db.query(Feedback)
            .filter(Feedback.embedding.is_(None))
            .all()
        )

        results = []
        for row in rows:
            if row.raw_text:
                row.embedding = self.embed_text(row.raw_text)
                results.append({
                    "id": row.id,
                    "embedded": True
                })

        self.db.commit()
        return results
