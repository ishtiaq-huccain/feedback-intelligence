from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/")
def semantic_search(
    query: str = Query(..., description="Search query text"),
    top_k: int = Query(5, description="Number of results"),
    product: str = Query(None, description="Optional product filter"),
    locale: str = Query(None, description="Optional locale filter"),
    db: Session = Depends(get_db),
):
    """
    Semantic search using pgvector cosine similarity.
    """
    service = SearchService(db)
    results = service.semantic_search(query, top_k=top_k, product=product, locale=locale)
    return {"query": query, "results": results}
