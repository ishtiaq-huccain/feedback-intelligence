from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.ml.embedding_service import EmbeddingService

router = APIRouter(prefix="/embeddings", tags=["embeddings"])

@router.post("/batch")
def embed_batch(limit: int = 50, db: Session = Depends(get_db)):
    """
    Generate embeddings for a limited number of feedback rows.
    """
    service = EmbeddingService(db)
    return {"embedded": service.generate_embeddings_batch(limit)}

@router.post("/all")
def embed_all(db: Session = Depends(get_db)):
    """
    Generate embeddings for all missing feedback rows.
    """
    service = EmbeddingService(db)
    return {"embedded": service.generate_all_embeddings()}
