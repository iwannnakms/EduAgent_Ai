from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(video_router, prefix="/api/v1")
app.include_router(rag_router, prefix="/api/v1")
app.include_router(roadmap_router, prefix="/api/v1")

# Frontend Integration
frontend_path = "frontend/dist"

if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
    
    @app.get("/{catchall:path}")
    async def serve_frontend(catchall: str):
        if not catchall.startswith("api/v1"):
            return FileResponse(f"{frontend_path}/index.html")
