from typing import List, Dict

from sqlalchemy.orm import Session

from backend.services.search_service import SearchService
from backend.ml.groq_client import groq_client


class RAGService:
    def __init__(self, db: Session):
        self.db = db
        self.retriever = SearchService(db)

    def build_prompt(self, query: str, chunks: List[Dict]) -> List[Dict[str, str]]:
        sources_text = "\n\n".join(
            [
                f"[Source {i+1} | {c.get('ref_type')}:{c.get('ref_id')} | {c.get('title')}]\n{c.get('text')}"
                for i, c in enumerate(chunks)
            ]
        )
        system = (
            "You are a helpful assistant. Answer the user's question using ONLY the provided sources."
            " If the answer is not in the sources, say you don't know."
        )
        user = (
            f"Question: {query}\n\n"
            f"Sources:\n{sources_text}\n\n"
            "Answer concisely and cite sources like [1], [2]."
        )
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    def ask(self, query: str, top_k: int = 5) -> Dict:
        chunks = self.retriever.retrieve_chunks(query=query, top_k=top_k)
        messages = self.build_prompt(query, chunks)
        answer = groq_client.chat(messages, temperature=0.2, max_tokens=800)
        sources = [
            {
                "ref_type": c.get("ref_type"),
                "ref_id": c.get("ref_id"),
                "title": c.get("title"),
                "similarity": c.get("similarity"),
            }
            for c in chunks
        ]
        return {"answer": answer, "sources": sources}


