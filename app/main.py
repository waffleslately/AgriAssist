from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.db.init_db import init_db
from app.api.v1.api import api_router

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up Indian Agri-Advisory Backend Infrastructure...")
    # Initialize PostGIS tables if running in direct auto-sync mode
    try:
        await init_db()
        logger.info("Database schema verified/initialized.")
    except Exception as e:
        logger.warning(f"Database auto-migration skipped or failed (may be running migrations separately): {e}")
    yield
    logger.info("Shutting down Agri-Advisory Backend Infrastructure...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    description="""
    ## India-Scoped Agri-Advisory Backend (Phase 1 MVP)
    
    Provides spatial plot management, Sentinel-2 Google Earth Engine NDVI ingestion, 
    Soil Health Card analysis, Open-Meteo rainfall forecasting, and ICAR-aligned 
    fertilizer recommendations converting target NPK into standard Indian bags (Urea, DAP, MOP).
    """
)

# Set CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Healthcheck
@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "gee_mode": "live" if settings.GEE_ENABLED else "developer_simulation"
    }

@app.get("/", tags=["Frontend"], include_in_schema=False)
@app.get("/app", tags=["Frontend"], include_in_schema=False)
async def serve_frontend():
    """Serve the AgriAssist web frontend."""
    return FileResponse(Path(__file__).parent.parent / "static" / "index.html")

# Mount static files (CSS, JS, assets)
static_dir = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Mount API V1 router
app.include_router(api_router, prefix=settings.API_V1_STR)
