from fastapi import Header, HTTPException, status
from backend.utils.logger import get_logger

logger = get_logger(__name__)

async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Simple header-based API key guard."""
    if not x_api_key:
        logger.warning("Unauthorized: missing X-API-Key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key"
        )
