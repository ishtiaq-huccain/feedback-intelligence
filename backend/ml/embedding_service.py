from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from backend.database.models import Feedback


class EmbeddingService:
    _model = None

    def __init__(self, db: Session):
        self.db = db

    @classmethod
    def get_model(cls):
        if cls._model is None:
            cls._model = SentenceTransformer(
                "sentence-transformers/all-MiniLM-L6-v2",
                device="cpu"
            )
        return cls._model

    def embed_text(self, text: str):
        model = self.get_model()

        embedding = model.encode(
            text,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False
        )

        return embedding.tolist()

    def embed(self, text: str):
        return self.embed_text(text)

    def generate_embeddings_batch(self, limit: int = 5):
        rows = (
            self.db.query(Feedback)
            .filter(
                Feedback.embedding.is_(None),
                Feedback.raw_text.isnot(None)
            )
            .limit(limit)
            .all()
        )

        if not rows:
            return []

        model = self.get_model()

        texts = [row.raw_text for row in rows]

        embeddings = model.encode(
            texts,
            batch_size=2,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False
        )

        results = []

        for row, embedding in zip(rows, embeddings):
            row.embedding = embedding.tolist()

            results.append({
                "id": row.id,
                "text": row.raw_text[:50],
                "embedded": True
            })

        self.db.commit()

        return results

    def generate_all_embeddings(self, batch_size: int = 5):
        results = []

        while True:
            rows = (
                self.db.query(Feedback)
                .filter(
                    Feedback.embedding.is_(None),
                    Feedback.raw_text.isnot(None)
                )
                .limit(batch_size)
                .all()
            )

            if not rows:
                break

            model = self.get_model()

            texts = [row.raw_text for row in rows]

            embeddings = model.encode(
                texts,
                batch_size=2,
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False
            )

            for row, embedding in zip(rows, embeddings):
                row.embedding = embedding.tolist()

                results.append({
                    "id": row.id,
                    "embedded": True
                })

            self.db.commit()

        return results
