from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import Optional

from backend.database.database import get_db
from backend.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ---------- KPIs ----------
@router.get(
    "/kpis",
    operation_id="analytics_kpis",
)
def kpis(
    start: Optional[date] = None,
    end: Optional[date] = None,
    product: Optional[str] = None,
    locale: Optional[str] = None,
    version: Optional[str] = None,
    db: Session = Depends(get_db),
):
    start_dt = datetime.combine(start, datetime.min.time()) if start else None
    end_dt = datetime.combine(end, datetime.max.time()) if end else None
    svc = AnalyticsService(db)
    return svc.kpis(start_dt, end_dt, product, locale, version)


# ---------- Sentiment Trend ----------
@router.get(
    "/trends/sentiment",
    operation_id="analytics_sentiment_trend",
)
def sentiment_trend(
    interval: str = Query("month", pattern="^(month|week)$"),
    start: Optional[date] = None,
    end: Optional[date] = None,
    product: Optional[str] = None,
    locale: Optional[str] = None,
    version: Optional[str] = None,
    db: Session = Depends(get_db),
):
    start_dt = datetime.combine(start, datetime.min.time()) if start else None
    end_dt = datetime.combine(end, datetime.max.time()) if end else None
    svc = AnalyticsService(db)
    return svc.sentiment_trend(interval, start_dt, end_dt, product, locale, version)


# ---------- Category Trend ----------
@router.get(
    "/trends/categories",
    operation_id="analytics_category_trend",
)
def category_trend(
    interval: str = Query("month", pattern="^(month|week)$"),
    start: Optional[date] = None,
    end: Optional[date] = None,
    product: Optional[str] = None,
    locale: Optional[str] = None,
    version: Optional[str] = None,
    top_n: int = 5,
    db: Session = Depends(get_db),
):
    start_dt = datetime.combine(start, datetime.min.time()) if start else None
    end_dt = datetime.combine(end, datetime.max.time()) if end else None
    svc = AnalyticsService(db)
    return svc.category_trend(interval, start_dt, end_dt, product, locale, version, top_n)


# ---------- Aspect Trend ----------
@router.get(
    "/trends/aspects",
    operation_id="analytics_aspect_trend",
)
def aspect_trend(
    interval: str = Query("month", pattern="^(month|week)$"),
    start: Optional[date] = None,
    end: Optional[date] = None,
    product: Optional[str] = None,
    locale: Optional[str] = None,
    version: Optional[str] = None,
    top_n: int = 5,
    db: Session = Depends(get_db),
):
    start_dt = datetime.combine(start, datetime.min.time()) if start else None
    end_dt = datetime.combine(end, datetime.max.time()) if end else None
    svc = AnalyticsService(db)
    return svc.aspect_trend(interval, start_dt, end_dt, product, locale, version, top_n)


# ---------- Drilldown ----------
@router.get(
    "/drilldown",
    operation_id="analytics_drilldown",
)
def drilldown(
    category: Optional[str] = None,
    aspect: Optional[str] = None,
    sentiment: Optional[str] = None,
    start: Optional[date] = None,
    end: Optional[date] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """
    Drill down to see representative feedback examples by category, aspect, sentiment, or date range.
    """
    start_dt = datetime.combine(start, datetime.min.time()) if start else None
    end_dt = datetime.combine(end, datetime.max.time()) if end else None

    service = AnalyticsService(db)
    results = service.get_drilldown(
        category=category,
        aspect=aspect,
        sentiment=sentiment,
        start=start_dt,
        end=end_dt,
        limit=limit,
    )
    return {"count": len(results), "results": results}


# ---------- Drilldown Export ----------
@router.get(
    "/drilldown/export",
    operation_id="analytics_drilldown_export",
)
def drilldown_export(
    category: Optional[str] = None,
    aspect: Optional[str] = None,
    sentiment: Optional[str] = None,
    start: Optional[date] = None,
    end: Optional[date] = None,
    limit: int = 1000,
    db: Session = Depends(get_db),
):
    """
    Export drilldown feedback as CSV based on filters.
    """
    start_dt = datetime.combine(start, datetime.min.time()) if start else None
    end_dt = datetime.combine(end, datetime.max.time()) if end else None

    service = AnalyticsService(db)
    return service.export_drilldown_csv(
        category=category,
        aspect=aspect,
        sentiment=sentiment,
        start=start_dt,
        end=end_dt,
        limit=limit,
    )
