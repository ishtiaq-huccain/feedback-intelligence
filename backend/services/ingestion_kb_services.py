from sqlalchemy.orm import Session
from backend.database import models
from backend.utils.chunker import chunk_text
from backend.ml.embedding_service import EmbeddingService
from datetime import datetime
from pathlib import Path
from PyPDF2 import PdfReader


def ingest_kb_doc(
    db: Session,
    source: str,
    file_path: str,
    content_type: str,
    title: str,
    metadata: dict = None
):
    """
    Ingest a knowledge base document (txt/md/pdf).
    Stores raw text in KBDoc, splits into chunks, embeds into KBChunk.
    """

    embedder = EmbeddingService(db)

    # 1. Extract raw text
    if content_type in ("txt", "md"):
        text = Path(file_path).read_text(encoding="utf-8")
    elif content_type == "pdf":
        reader = PdfReader(file_path)
        text = "\n".join(
            [page.extract_text() for page in reader.pages if page.extract_text()]
        )
    else:
        raise ValueError(f"Unsupported content type: {content_type}")

    # 2. Create doc record
    doc = models.KBDoc(
        title=title,
        source=source,
        content_type=content_type,
        path=file_path,
        raw_text=text,
        doc_metadata=metadata or {},
        created_at=datetime.utcnow()
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 3. Chunk + embed
    chunks = chunk_text(text, chunk_size=300, overlap=50)
    for idx, chunk in enumerate(chunks):
        embedding = embedder.embed_text(chunk)   # ✅ now using embed_text
        db.add(
            models.KBChunk(
                doc_id=doc.id,
                chunk_index=idx,
                text=chunk,
                embedding=embedding
            )
        )

    db.commit()
    return doc
