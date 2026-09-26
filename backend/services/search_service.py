from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Optional

from backend.ml.embedding_service import EmbeddingService


class SearchService:
    def __init__(self, db: Session):
        self.db = db
        # Reuse the same embedder as ingestion (bge-small-en-v1.5 with normalization)
        self.embedder = EmbeddingService(db)

    def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        product: Optional[str] = None,
        locale: Optional[str] = None,
    ) -> List[Dict]:
        """
        Search top_k most similar items across the unified search index.
        Returns mixed results (feedback and kb chunks).
        Optional product/locale filters apply only to feedback entries (when metadata present).
        """
        query_embedding = self.embedder.embed_text(query)

        sql = """
        SELECT id, ref_type, ref_id, title, text, metadata,
               1 - (embedding <=> (:query_embedding)::vector) AS similarity
        FROM search_index
        WHERE embedding IS NOT NULL
        {filters}
        ORDER BY embedding <=> (:query_embedding)::vector
        LIMIT :top_k;
        """

        filter_clauses = []
        params = {
            "query_embedding": query_embedding,
            "top_k": top_k,
        }

        # Apply JSON metadata filters where available (only affects feedback rows that stored them)
        if product:
            filter_clauses.append("AND (metadata->>'product' IS NULL OR metadata->>'product' = :product)")
            params["product"] = product
        if locale:
            filter_clauses.append("AND (metadata->>'locale' IS NULL OR metadata->>'locale' = :locale)")
            params["locale"] = locale

        filter_sql = " ".join(filter_clauses)
        sql = sql.format(filters=filter_sql)

        rows = self.db.execute(text(sql), params).fetchall()

        results: List[Dict] = []
        for row in rows:
            results.append(
                {
                    "id": row.id,
                    "ref_type": row.ref_type,
                    "ref_id": row.ref_id,
                    "title": row.title,
                    "text": row.text,
                    "metadata": row.metadata,
                    "similarity": float(row.similarity),
                }
            )
        return results

    def retrieve_chunks(
        self,
        query: str,
        top_k: int = 5,
        product: Optional[str] = None,
        locale: Optional[str] = None,
    ) -> List[Dict]:
        """
        Convenience wrapper that returns top_k entries with text and minimal metadata
        from the unified search index for RAG consumption.
        """
        results = self.semantic_search(query=query, top_k=top_k, product=product, locale=locale)
        # Normalize shape for RAG: include source hints
        normalized: List[Dict] = []
        for item in results:
            normalized.append(
                {
                    "ref_type": item.get("ref_type"),
                    "ref_id": item.get("ref_id"),
                    "title": item.get("title"),
                    "text": item.get("text"),
                    "metadata": item.get("metadata"),
                    "similarity": item.get("similarity"),
                }
            )
        return normalized
