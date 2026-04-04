import json
import logging
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
            "Return only valid JSON.\n\n"
            f"Topic: {topic}\n"
            f"Learner level: {learner_level}\n"
            f"Target duration (weeks): {target_duration_weeks}"
        )
        
        try:
            response = self.client.models.generate_content(
                model=self.chat_model_name,
                contents=prompt
            )
            raw = response.text or "{}"
            
            # Clean up JSON if LLM wraps it in markdown
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
            logger.error(f"Failed to generate roadmap: {str(e)}")
            raise RuntimeError(f"Roadmap generation failed: {str(e)}")
