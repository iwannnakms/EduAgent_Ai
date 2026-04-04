from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.rag import router as rag_router
from app.api.routes.roadmap import router as roadmap_router
from app.api.routes.video import router as video_router
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(video_router, prefix="/api/v1")
app.include_router(rag_router, prefix="/api/v1")
app.include_router(roadmap_router, prefix="/api/v1")
