from __future__ import annotations

from typing import Dict, List, Tuple
import re

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.services.search_service import SearchService
from backend.ml.groq_client import groq_client


WHITELISTED_STATS = {
    "sentiment_trend": True,
    "top_categories": True,
}


class AgentAskService:
    def __init__(self, db: Session):
        self.db = db
        self.search = SearchService(db)

    # ---- Planner ----
    def plan(self, question: str) -> Dict[str, bool]:
        q = question.lower()
        needs_stats = any(
            kw in q
            for kw in ["trend", "drop", "increase", "decrease", "last month", "by month", "in july", "over time"]
        )
        # Trigger stats/examples for "top complaints" style queries
        if any(kw in q for kw in ["top complaint", "top complaints", "top issues", "most common", "most frequent", "top"]):
            needs_stats = True
        needs_examples = any(kw in q for kw in ["example", "examples", "show", "give me", "list", "complaint", "complaints"])
        needs_rag = any(kw in q for kw in ["why", "explain", "what are", "how", "details", "root cause"]) or not (
            needs_stats or needs_examples
        )
        return {"stats": needs_stats, "examples": needs_examples, "rag": needs_rag}

    # ---- Safe Stats (whitelisted) ----
    def compute_stats(self, question: str) -> Dict:
        """
        Provide only whitelisted aggregations using parameterized SQL.
        - sentiment_trend: by month counts per sentiment
        - top_categories: top 5 categories overall or filtered by keyword in text
        """
        q = question.lower()
        keyword = self._extract_topic_keyword(q)

        # Sentiment trend by month (last 12 months)
        trend_sql = text(
            """
            SELECT to_char(date_trunc('month', created_at), 'YYYY-MM') AS month,
                   sentiment,
                   COUNT(*) AS count
            FROM feedback
            WHERE created_at IS NOT NULL
              AND sentiment IS NOT NULL
              {kw_filter}
            GROUP BY 1, 2
            ORDER BY 1 ASC
            """.format(
                kw_filter=" AND raw_text ILIKE :kw " if keyword else ""
            )
        )
        params = {"kw": f"%{keyword}%"} if keyword else {}
        trend_rows = self.db.execute(trend_sql, params).fetchall()
        sentiment_trend: Dict[str, Dict[str, int]] = {}
        for r in trend_rows:
            month = r.month
            sentiment_trend.setdefault(month, {"positive": 0, "neutral": 0, "negative": 0})
            sentiment_trend[month][(r.sentiment or "").lower()] = int(r.count)

        # Top categories (optional keyword filter)
        cat_sql = text(
            """
            SELECT category, COUNT(*) AS count
            FROM feedback
            WHERE category IS NOT NULL
            {kw_filter}
            GROUP BY category
            ORDER BY count DESC
            LIMIT 5
            """.format(
                kw_filter=" AND raw_text ILIKE :kw " if keyword else ""
            )
        )
        cat_rows = self.db.execute(cat_sql, params).fetchall()
        top_categories = [{"category": r.category, "count": int(r.count)} for r in cat_rows]

        return {"sentiment_trend": sentiment_trend, "top_categories": top_categories, "keyword": keyword}

    # ---- Examples ----
    def get_examples(self, question: str, limit: int = 5) -> List[Dict]:
        topic = self._extract_topic_keyword(question.lower())
        if topic:
            sql = text(
                """
                SELECT id, raw_text, sentiment, category, created_at
                FROM feedback
                WHERE raw_text ILIKE :kw
                ORDER BY created_at DESC NULLS LAST
                LIMIT :limit
                """
            )
            rows = self.db.execute(sql, {"kw": f"%{topic}%", "limit": limit}).fetchall()
            return [
                {
                    "id": r.id,
                    "text": r.raw_text,
                    "sentiment": r.sentiment,
                    "category": r.category,
                    "created_at": str(r.created_at) if r.created_at else None,
                }
                for r in rows
            ]
        # fallback to semantic search over unified index → feedback only
        results = self.search.retrieve_chunks(query=question, top_k=limit)
        examples = [r for r in results if r.get("ref_type") == "feedback"]
        return examples[:limit]

    # ---- RAG ----
    def run_rag(self, question: str, top_k: int = 5) -> Tuple[str, List[Dict]]:
        chunks = self.search.retrieve_chunks(query=question, top_k=top_k)
        messages = self._build_rag_prompt(question, chunks)
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
        return answer, sources

    # ---- Orchestrator ----
    def ask(self, question: str) -> Dict:
        plan = self.plan(question)
        stats: Dict | None = None
        examples: List[Dict] | None = None
        rag_answer: str | None = None
        sources: List[Dict] | None = None

        if plan.get("stats"):
            stats = self.compute_stats(question)
        if plan.get("examples"):
            examples = self.get_examples(question, limit=5)
        if plan.get("rag"):
            rag_answer, sources = self.run_rag(question, top_k=5)

        # Compose final answer with LLM for coherence
        messages = self._build_final_prompt(question, stats or {}, examples or [], rag_answer or "")
        final_answer = groq_client.chat(messages, temperature=0.1, max_tokens=900)

        # Append explicit citations block mapped to sources if present
        if sources:
            citation_lines = [
                f"[{i+1}] {s.get('ref_type')}:{s.get('ref_id')} - {s.get('title')} (sim {round(float(s.get('similarity') or 0), 2)})"
                for i, s in enumerate(sources)
            ]
            final_answer = final_answer.rstrip() + "\n\nCitations\n" + "\n".join(citation_lines)

        return {
            "answer": final_answer,
            "plan": plan,
            "stats": stats,
            "examples": examples,
            "sources": sources,
        }

    # ---- Helpers ----
    def _extract_topic_keyword(self, q: str) -> str | None:
        # naive extraction: grab quoted phrase or word after "about"/"on"
        m = re.search(r'"([^"]+)"', q)
        if m:
            return m.group(1)
        m = re.search(r"about ([a-z0-9 _-]+)", q)
        if m:
            return m.group(1).strip()
        m = re.search(r"on ([a-z0-9 _-]+)", q)
        if m:
            return m.group(1).strip()
        return None

    def _build_rag_prompt(self, question: str, chunks: List[Dict]) -> List[Dict[str, str]]:
        sources_text = "\n\n".join(
            [
                f"[Source {i+1} | {c.get('ref_type')}:{c.get('ref_id')} | {c.get('title')}]\n{c.get('text')}"
                for i, c in enumerate(chunks)
            ]
        )
        return [
            {"role": "system", "content": "You are a helpful assistant that uses provided sources only."},
            {
                "role": "user",
                "content": f"Question: {question}\n\nSources:\n{sources_text}\n\nAnswer concisely and cite sources like [1], [2].",
            },
        ]

    def _build_final_prompt(self, question: str, stats: Dict, examples: List[Dict], rag_answer: str) -> List[Dict[str, str]]:
        return [
            {"role": "system", "content": "You synthesize analytics and RAG into one clear answer."},
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n\n"
                    f"Stats JSON: {stats}\n\n"
                    f"Examples (first 3): {examples[:3]}\n\n"
                    f"RAG Answer: {rag_answer}\n\n"
                    "Compose: 1) Summary, 2) Likely drivers (based on stats + sources), 3) Short examples, 4) Citations refs if present."
                ),
            },
        ]


