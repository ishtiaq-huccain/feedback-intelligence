from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.services.rag_service import RAGService


router = APIRouter(prefix="/rag", tags=["rag"])


@router.get("/ask")
def ask(query: str = Query(..., description="User question"), top_k: int = 5, db: Session = Depends(get_db)):
    try:
        service = RAGService(db)
        result = service.ask(query=query, top_k=top_k)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


