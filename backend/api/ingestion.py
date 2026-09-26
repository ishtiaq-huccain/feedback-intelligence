from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import pandas as pd
import io, json

from backend.database.database import get_db
from backend.services.ingestion_service import ingest_feedback
from backend.api.schemas import IngestionRunRead

router = APIRouter(prefix="/ingest", tags=["Ingestion"])


@router.post("/feedback", response_model=IngestionRunRead)
async def ingest_feedback_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a CSV or JSON file of feedback records and ingest into DB.
    Returns an ingestion summary.
    """
    try:
        if file.filename.endswith(".csv"):
            content = await file.read()
            df = pd.read_csv(io.BytesIO(content))
            records = df.to_dict(orient="records")
        elif file.filename.endswith(".json"):
            content = await file.read()
            records = json.loads(content)
            if not isinstance(records, list):
                raise ValueError("JSON must be a list of records")
        else:
            raise HTTPException(status_code=400, detail="Only CSV or JSON supported")

        run = ingest_feedback(db, source="upload", records=records)
        return run
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
