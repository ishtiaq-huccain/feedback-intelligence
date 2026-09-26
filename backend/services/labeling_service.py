import json
from pathlib import Path
from sqlalchemy.orm import Session
from backend.database.models import Feedback
from backend.ml.groq_client import GroqClient

# Load taxonomy
TAXONOMY_DIR = Path("data/taxonomy")
CATEGORIES = json.loads((TAXONOMY_DIR / "categories.json").read_text())
ASPECTS = json.loads((TAXONOMY_DIR / "aspects.json").read_text())


class LabelingService:
    def __init__(self, db: Session):
        self.db = db
        self.client = GroqClient()

    def label_feedback_item(self, feedback_text: str) -> dict:
        """
        Send feedback text to Groq and return parsed labels based on taxonomy.
        """
        if not feedback_text or not feedback_text.strip():
            # Handle empty feedback gracefully
            return {"sentiment": "neutral", "category": None, "aspects": []}

        prompt = f"""
        You are an AI that labels product feedback.

        - Sentiment: one of ["positive", "negative", "neutral"]
        - Category: choose ONE from this list: {CATEGORIES}
        - Aspects: choose one or more from this list: {ASPECTS}

        Respond ONLY in valid JSON strictly matching this schema:
        {{
          "sentiment": "positive|negative|neutral",
          "category": "one_of_categories",
          "aspects": ["subset_of_aspects"]
        }}

        Feedback: "{feedback_text}"
        """

        response = self.client.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=512,
            stream=False,
        )

        try:
            parsed = json.loads(response)
            # Ensure keys exist even if LLM misses them
            return {
                "sentiment": parsed.get("sentiment", "neutral"),
                "category": parsed.get("category"),
                "aspects": parsed.get("aspects", []),
            }
        except Exception:
            # fallback if Groq output is malformed
            return {"sentiment": "neutral", "category": None, "aspects": []}

    def run_batch_labeling(self):
        """
        Label all unlabeled feedback rows.
        """
        unlabeled = (
            self.db.query(Feedback)
            .filter(Feedback.sentiment.is_(None))
            .all()
        )

        results = []
        for item in unlabeled:
            labels = self.label_feedback_item(item.raw_text)

            item.sentiment = labels["sentiment"]
            item.category = labels["category"]
            item.aspects = labels["aspects"]
            item.sentiment_conf = 0.9 if labels["sentiment"] else 0.0
            item.category_conf = 0.9 if labels["category"] else 0.0

            results.append(
                {
                    "id": item.id,
                    "sentiment": item.sentiment,
                    "category": item.category,
                    "aspects": item.aspects,
                }
            )

        self.db.commit()
        return results

    def run_incremental_labeling(self, limit: int = 50):
        """
        Label only a limited number of new/unlabeled feedback.
        """
        unlabeled = (
            self.db.query(Feedback)
            .filter(Feedback.sentiment.is_(None))
            .limit(limit)
            .all()
        )

        results = []
        for item in unlabeled:
            labels = self.label_feedback_item(item.raw_text)

            item.sentiment = labels["sentiment"]
            item.category = labels["category"]
            item.aspects = labels["aspects"]
            item.sentiment_conf = 0.9 if labels["sentiment"] else 0.0
            item.category_conf = 0.9 if labels["category"] else 0.0

            results.append(
                {
                    "id": item.id,
                    "sentiment": item.sentiment,
                    "category": item.category,
                    "aspects": item.aspects,
                }
            )

        self.db.commit()
        return results
