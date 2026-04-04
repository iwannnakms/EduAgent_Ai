from functools import lru_cache
from typing import Iterable
from app.utils.gemini_client import get_gemini_client

def _normalize(name: str) -> str:
    return name.removeprefix("models/")

def _pick_preferred(available: Iterable[str], preferred: str) -> str | None:
    preferred_norm = _normalize(preferred)
    for name in available:
        if _normalize(name) == preferred_norm:
            return name
    for name in available:
        if preferred_norm in _normalize(name):
            return name
    return None

@lru_cache(maxsize=16)
def resolve_model(preferred: str, method: str) -> str:
    client = get_gemini_client()
    candidates: list[str] = []
    
    # In new SDK, method names like 'generateContent' are mapped to capabilities
    # For simplicity, we'll fetch all models and filter by prefix/name
    # Or just return the preferred if it exists
    try:
        models = client.models.list()
        for m in models:
            # The new SDK models have different attribute names
            # We'll just collect the names for now
            candidates.append(m.name)
    except Exception:
        # Fallback to just returning the preferred if list fails
        return _normalize(preferred)

    if not candidates:
        return _normalize(preferred)

    preferred_match = _pick_preferred(candidates, preferred)
    res = _normalize(preferred_match) if preferred_match else _normalize(preferred)
    print(f"DEBUG: resolve_model(preferred='{preferred}') -> '{res}'")
    return res
