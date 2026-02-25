"""
Weather Forecast ML API - FastAPI Application
Predicts daily weather using trained ML models
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging
import time
from datetime import datetime

from app.routers import forecast, health, model_management
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.metrics import metrics_middleware
from app.services.model_registry import ModelRegistry

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("🚀 Starting Weather Forecast ML API...")
    setup_logging()

    # Load model on startup
    registry = ModelRegistry()
    await registry.load_latest_model()
    app.state.model_registry = registry

    logger.info("✅ API ready to serve predictions")
    yield

    logger.info("🛑 Shutting down Weather Forecast ML API...")

app = FastAPI(
    title="Weather Forecast ML API",
    description="Daily weather prediction using Machine Learning",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.middleware("http")(metrics_middleware)

# Routers
app.include_router(forecast.router, prefix="/api/v1/forecast", tags=["Forecast"])
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(model_management.router, prefix="/api/v1/models", tags=["Models"])

@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "Weather Forecast ML API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        workers=settings.WORKERS,
    )
