from typing import Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
from collections import Counter, defaultdict
from backend.database.models import Feedback
import csv
import io
import json
from fastapi.responses import StreamingResponse
from datetime import datetime


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    # ---------- Internal: apply common filters ----------
    def _apply_filters(
        self,
        query,
        start: Optional[datetime],
        end: Optional[datetime],
        product: Optional[str],
        locale: Optional[str],
        version: Optional[str],
    ):
        if start:
            query = query.filter(Feedback.created_at >= start)
        if end:
            query = query.filter(Feedback.created_at <= end)
        if product:
            query = query.filter(Feedback.product == product)
        if locale:
            query = query.filter(Feedback.locale == locale)
        if version:
            query = query.filter(Feedback.version == version)
        return query

    # ---------- KPIs ----------
    def kpis(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        product: Optional[str] = None,
        locale: Optional[str] = None,
        version: Optional[str] = None,
    ):
        q = self._apply_filters(self.db.query(Feedback), start, end, product, locale, version)
        total = q.count()
        neg = q.filter(Feedback.sentiment == "negative").count()
        pos = q.filter(Feedback.sentiment == "positive").count()
        neu = q.filter(Feedback.sentiment == "neutral").count()

        # Top categories (respecting the same filters)
        top_categories = (
            self._apply_filters(
                self.db.query(Feedback.category, func.count(Feedback.id)),
                start, end, product, locale, version
            )
            .group_by(Feedback.category)
            .order_by(func.count(Feedback.id).desc())
            .limit(5)
            .all()
        )

        # Top aspects from JSONB array (respecting the same filters)
        top_aspects = (
            self._apply_filters(
                self.db.query(
                    func.jsonb_array_elements_text(Feedback.aspects).label("aspect"),
                    func.count(Feedback.id),
                ),
                start, end, product, locale, version
            )
            .group_by("aspect")
            .order_by(func.count(Feedback.id).desc())
            .limit(5)
            .all()
        )

        return {
            "total_feedback": total,
            "percent_negative": (neg / total * 100 if total else 0),
            "percent_positive": (pos / total * 100 if total else 0),
            "percent_neutral": (neu / total * 100 if total else 0),
            "top_categories": [{"category": c or "unknown", "count": cnt} for c, cnt in top_categories],
            "top_aspects": [{"aspect": a or "unknown", "count": cnt} for a, cnt in top_aspects],
        }

    # ---------- Sentiment Trend ----------
    def sentiment_trend(
        self,
        interval: str = "month",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        product: Optional[str] = None,
        locale: Optional[str] = None,
        version: Optional[str] = None,
    ):
        bucket = func.date_trunc("week" if interval == "week" else "month", Feedback.created_at).label("bucket")

        rows = (
            self._apply_filters(
                self.db.query(bucket, Feedback.sentiment, func.count(Feedback.id)),
                start, end, product, locale, version
            )
            .group_by(bucket, Feedback.sentiment)
            .order_by(bucket)
            .all()
        )

        trend: Dict[str, Dict[str, int]] = {}
        for bkt, sentiment, count in rows:
            key = bkt.strftime("%Y-%m-%d")
            if key not in trend:
                trend[key] = {"positive": 0, "negative": 0, "neutral": 0, "unknown": 0}
            trend[key][(sentiment or "unknown")] += count

        return dict(sorted(trend.items()))

    # ---------- Category Trend ----------
    def category_trend(
        self,
        interval: str = "month",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        product: Optional[str] = None,
        locale: Optional[str] = None,
        version: Optional[str] = None,
        top_n: int = 5,
    ):
        bucket = func.date_trunc("week" if interval == "week" else "month", Feedback.created_at).label("bucket")

        rows = (
            self._apply_filters(
                self.db.query(bucket, Feedback.category, func.count(Feedback.id)),
                start, end, product, locale, version
            )
            .group_by(bucket, Feedback.category)
            .order_by(bucket)
            .all()
        )

        from collections import defaultdict, Counter
        trend: Dict[str, Dict[str, int]] = defaultdict(dict)
        for bkt, category, count in rows:
            key = bkt.strftime("%Y-%m-%d")
            cat = category or "unknown"
            trend[key][cat] = trend[key].get(cat, 0) + count

        all_counts = Counter()
        for cats in trend.values():
            for cat, cnt in cats.items():
                all_counts[cat] += cnt
        keep = {c for c, _ in all_counts.most_common(top_n)}

        filtered_trend = {}
        for k, cats in trend.items():
            filtered_trend[k] = {cat: cnt for cat, cnt in cats.items() if cat in keep}

        return dict(sorted(filtered_trend.items()))

    # ---------- Aspect Trend ----------
    def aspect_trend(
        self,
        interval: str = "month",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        product: Optional[str] = None,
        locale: Optional[str] = None,
        version: Optional[str] = None,
        top_n: int = 5,
    ):
        bucket = func.date_trunc("week" if interval == "week" else "month", Feedback.created_at).label("bucket")

        rows = (
            self._apply_filters(
                self.db.query(
                    bucket,
                    func.jsonb_array_elements_text(Feedback.aspects).label("aspect"),
                    func.count(Feedback.id),
                ),
                start, end, product, locale, version
            )
            .group_by(bucket, "aspect")
            .order_by(bucket)
            .all()
        )

        from collections import defaultdict, Counter
        trend: Dict[str, Dict[str, int]] = defaultdict(dict)
        for bkt, aspect, count in rows:
            key = bkt.strftime("%Y-%m-%d")
            asp = aspect or "unknown"
            trend[key][asp] = trend[key].get(asp, 0) + count

        all_counts = Counter()
        for aspects in trend.values():
            for asp, cnt in aspects.items():
                all_counts[asp] += cnt
        keep = {a for a, _ in all_counts.most_common(top_n)}

        filtered_trend = {}
        for k, aspects in trend.items():
            filtered_trend[k] = {asp: cnt for asp, cnt in aspects.items() if asp in keep}

        return dict(sorted(filtered_trend.items()))

    # ---------- Drilldown (list) ----------
    def get_drilldown(
        self,
        category: Optional[str] = None,
        aspect: Optional[str] = None,
        sentiment: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 20,
        offset: int = 0,
    ):
        query = self._apply_filters(self.db.query(Feedback), start, end, product=None, locale=None, version=None)

        if category:
            query = query.filter(Feedback.category == category)
        if aspect:
            # aspects is JSONB array; match if contains the aspect value
            query = query.filter(Feedback.aspects.contains([aspect]))
        if sentiment:
            query = query.filter(Feedback.sentiment == sentiment)

        rows = query.order_by(Feedback.created_at.desc()).offset(offset).limit(limit).all()

        return [
            {
                "id": r.id,
                "raw_text": r.raw_text,
                "sentiment": r.sentiment or "unknown",
                "category": r.category or "unknown",
                "aspects": r.aspects or [],
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "product": r.product,
                "locale": r.locale,
                "version": r.version,
            }
            for r in rows
        ]

    # ---------- Drilldown Export (CSV) ----------
    def export_drilldown_csv(
        self,
        category: Optional[str] = None,
        aspect: Optional[str] = None,
        sentiment: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 1000,
    ):
        rows = self.get_drilldown(
            category=category,
            aspect=aspect,
            sentiment=sentiment,
            start=start,
            end=end,
            limit=limit,
        )

        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=["id", "raw_text", "sentiment", "category", "aspects", "created_at", "product", "locale", "version"],
        )
        writer.writeheader()
        for row in rows:
            row = dict(row)  # ensure mutable copy
            row["aspects"] = json.dumps(row["aspects"])  # serialize list for CSV
            writer.writerow(row)

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=drilldown_export.csv"},
        )
