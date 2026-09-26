from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.services.labeling_service import LabelingService

router = APIRouter(prefix="/labeling", tags=["labeling"])


@router.post("/batch")
def run_batch_labeling(db: Session = Depends(get_db)):
    """
    Label all unlabelled feedback in the database.
    """
    service = LabelingService(db)
    results = service.run_batch_labeling()
    return {"labeled": len(results), "results": results}


@router.post("/incremental")
def run_incremental_labeling(limit: int = 50, db: Session = Depends(get_db)):
    """
    Label only a limited number of unlabelled feedback.
    """
    service = LabelingService(db)
    results = service.run_incremental_labeling(limit=limit)
    return {"labeled": len(results), "results": results}
