from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.config import get_settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Engine & session factory
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Base for SQLAlchemy models
Base = declarative_base()

def get_db() -> Generator:
    """FastAPI dependency yielding a DB session, always closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_pgvector_extension() -> bool:
    """
    Try to enable pgvector (CREATE EXTENSION IF NOT EXISTS vector).
    Returns True if extension exists or was created; False otherwise.
    """
    if not settings.use_pgvector:
        logger.info("pgvector disabled via USE_PGVECTOR=false")
        return False

    if engine.url.get_backend_name() != "postgresql":
        logger.warning("pgvector requires PostgreSQL; current dialect: %s", engine.url.get_backend_name())
        return False

    try:
        with engine.begin() as conn:
            conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector;")
        logger.info("pgvector extension ready.")
        return True
    except Exception as e:
        logger.warning("Could not ensure pgvector extension (continuing without it): %s", e)
        return False


def bootstrap_schema() -> None:
    """
    Import models, ensure extension (if possible), and create tables.
    Safe to call multiple times.
    """
    # Import models so SQLAlchemy knows about them before create_all
    from backend.database import models  # noqa: F401

    ensure_pgvector_extension()
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema ensured (create_all).")
