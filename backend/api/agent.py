from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.services.agent_service import AgentAskService


router = APIRouter(prefix="/ask", tags=["ask"])


@router.get("/agent")
def agent_ask(query: str = Query(..., description="User question"), db: Session = Depends(get_db)):
    try:
        service = AgentAskService(db)
        result = service.ask(query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


