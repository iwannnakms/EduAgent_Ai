import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

@lru_cache(maxsize=16)
def resolve_model(preferred: str, method: str) -> str:
    """
    ULTRA-STRICT RESOLVER:
    Uses the exact names verified for your account to stop 404 errors.
    """
    # Force the verified embedding model for ALL embedding requests
    if "embed" in method.lower() or "embedding" in preferred.lower():
        resolved = "gemini-embedding-001"
    # Force the verified flash model for ALL generation requests
    else:
        resolved = "gemini-flash-latest"
        
    logger.info(f"Resolved model for {method}: Forced to '{resolved}'")
    return resolved
