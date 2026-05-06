import json
import logging
import time
from typing import Any, Dict

from app.core.config import get_settings
from app.utils.gemini_client import get_gemini_client
from app.utils.gemini_models import resolve_model
from app.utils.semantic_cache import SemanticCache

logger = logging.getLogger(__name__)

class RoadmapService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = get_gemini_client()
        self.chat_model_name = resolve_model(self.settings.gemini_chat_model, "generateContent")
        self.cache = SemanticCache()

    def generate_roadmap(self, topic: str, learner_level: str, target_duration_weeks: int) -> Dict[str, Any]:
        cache_key = f"{topic}|{learner_level}|{target_duration_weeks}"
        cached = self.cache.get(scope="roadmap", query=cache_key)
        if cached:
            response = cached["response"]
            response["cache_hit"] = True
            return response

        prompt = (
            "Generate a learning roadmap as strict JSON with keys: "
            "topic, learner_level, total_weeks, steps. "
            "Each step must include step (number), title, outcomes (list), resources (list), estimated_hours (number). "
            "CRITICAL: For every item in the 'resources' list, provide a valid direct URL link to documentation, a tutorial, or a specific course (e.g. 'https://react.dev'). "
            "Return only valid JSON.\n\n"
            f"Topic: {topic}\n"
            f"Learner level: {learner_level}\n"
            f"Target duration (weeks): {target_duration_weeks}"
        )
        
        # Robust retry logic for 503/429 errors
        max_retries = 5
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.chat_model_name,
                    contents=prompt
                )
                raw = response.text or "{}"
                
                if "```" in raw:
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                    raw = raw.strip()
                
                payload = json.loads(raw)
                payload["cache_hit"] = False
                self.cache.set(scope="roadmap", query=cache_key, response=payload)
                return payload
            except Exception as e:
                last_error = e
                # Retry on 503 (Busy) or 429 (Rate Limit)
                if "503" in str(e) or "429" in str(e):
                    wait_time = (attempt + 1) * 3
                    logger.warning(f"Gemini busy (attempt {attempt+1}/{max_retries}). Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                break

        logger.error(f"Failed to generate roadmap after retries: {str(last_error)}")
        raise RuntimeError(f"Roadmap generation failed: {str(last_error)}")
