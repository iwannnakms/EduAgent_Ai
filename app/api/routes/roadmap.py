from fastapi import APIRouter

from app.models.schemas import RoadmapRequest, RoadmapResponse
from app.services.roadmap_service import RoadmapService

router = APIRouter(prefix="/roadmap", tags=["roadmap"])


@router.post("/generate", response_model=RoadmapResponse)
async def generate_roadmap(payload: RoadmapRequest) -> RoadmapResponse:
    service = RoadmapService()
    result = service.generate_roadmap(
        topic=payload.topic,
        learner_level=payload.learner_level,
        target_duration_weeks=payload.target_duration_weeks,
    )
    result.pop("cache_hit", None)
    return RoadmapResponse(**result)
