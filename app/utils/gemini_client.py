from google import genai
from app.core.config import get_settings

def get_gemini_client() -> genai.Client:
    """
    Returns a Gemini client using the default API version (v1beta) 
    which is required for the latest models in the new SDK.
    """
    settings = get_settings()
    return genai.Client(api_key=settings.gemini_api_key)
