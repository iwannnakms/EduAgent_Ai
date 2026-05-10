from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.api.routes.health import router as health_router
from app.api.routes.rag import router as rag_router
from app.api.routes.roadmap import router as roadmap_router
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name)

# Allow all origins for local development and cloud deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False, # Must be False if allow_origins is ["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Register API Routes FIRST (order matters in FastAPI)
app.include_router(health_router, prefix="/api/v1")
app.include_router(rag_router, prefix="/api/v1")
app.include_router(roadmap_router, prefix="/api/v1")

# 2. Serve Frontend (Only if build exists)
frontend_path = "frontend/dist"

if os.path.exists(frontend_path):
    logger.info(f"Serving frontend from {frontend_path}")
    # Mount the assets folder specifically
    if os.path.exists(f"{frontend_path}/assets"):
        app.mount("/assets", StaticFiles(directory=f"{frontend_path}/assets"), name="assets")

    # Serve the main index.html for all other non-API routes
    @app.get("/{catchall:path}")
    async def serve_frontend(catchall: str):
        if catchall.startswith("api/v1"):
            # This should have been caught by the routers above
            return {"error": "API route not found"}
        
        # Check if the requested file exists (e.g. favicon.ico)
        potential_file = os.path.join(frontend_path, catchall)
        if os.path.isfile(potential_file):
            return FileResponse(potential_file)
            
        return FileResponse(f"{frontend_path}/index.html")
else:
    logger.warning(f"Frontend path {frontend_path} not found. UI will not be served by backend.")
    @app.get("/")
    async def root_fallback():
        return {"message": "API is running. Frontend build not found. Run 'npm run build' in frontend folder."}
