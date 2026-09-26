from fastapi import APIRouter
from backend.api import labeling, embedding, search, analytics, indexer, ingestion_kb, ingestion, rag, agent

router = APIRouter()

# Mount feature routers without extra prefixes/tags to avoid duplicate Swagger entries
router.include_router(labeling.router)
router.include_router(embedding.router)
router.include_router(search.router)
router.include_router(analytics.router)
router.include_router(indexer.router)
router.include_router(ingestion.router)

# Knowledge Base ingestion routes (already have their own prefix/tags)
router.include_router(ingestion_kb.router)
router.include_router(rag.router)
router.include_router(agent.router)
