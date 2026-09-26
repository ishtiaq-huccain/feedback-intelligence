from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path
import os

from backend.database.database import get_db
from backend.services.ingestion_kb_services import ingest_kb_doc

# Separate KB ingestion group
router = APIRouter(
    prefix="/ingest/docs",
    tags=["Knowledge Base Ingestion"]
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/", summary="Ingest a knowledge base document")
async def ingest_doc(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload a TXT, MD, or PDF document to ingest into Knowledge Base docs.
    The document is stored, chunked, and embedded for retrieval.
    """
    try:
        ext = file.filename.split(".")[-1].lower()
        if ext not in ["txt", "md", "pdf"]:
            raise HTTPException(status_code=400, detail="Only txt, md, pdf supported")

        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        doc = ingest_kb_doc(
            db,
            source="upload",
            file_path=file_path,
            content_type=ext,
            title=file.filename
        )
        return {
            "id": doc.id,
            "title": doc.title,
            "chunks": len(doc.chunks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
