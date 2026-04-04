from google import genai
from app.core.config import get_settings

def get_gemini_client() -> genai.Client:
    settings = get_settings()
    # Using v1beta as embedding models require this endpoint in this environment
    return genai.Client(
        api_key=settings.gemini_api_key,
        http_options={'api_version': 'v1beta'}
    )
