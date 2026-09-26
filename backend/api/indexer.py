from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.services.indexer_service import IndexerService

router = APIRouter(prefix="/indexer", tags=["indexer"])


@router.post("/feedback")
def index_feedback(limit: int = 1000, db: Session = Depends(get_db)):
    """
    Index feedback rows into the unified search index.
    """
    service = IndexerService(db)
    count = service.index_feedback(limit=limit)
    return {"indexed_feedback": count}


@router.post("/kb")
def index_kb_chunks(limit: int = 1000, db: Session = Depends(get_db)):
    """
    Index KB chunks into the unified search index.
    """
    service = IndexerService(db)
    count = service.index_kb_chunks(limit=limit)
    return {"indexed_kb_chunks": count}
