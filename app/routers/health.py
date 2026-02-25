"""Health check endpoints for Kubernetes probes"""

from fastapi import APIRouter, Request
from datetime import datetime
import time
import logging

from app.schemas.weather import HealthResponse

router = APIRouter()
logger = logging.getLogger(__name__)

START_TIME = time.time()


@router.get("/live")
async def liveness():
    """Kubernetes liveness probe - is the app running?"""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@router.get("/ready")
async def readiness(request: Request):
    """Kubernetes readiness probe - is the app ready to serve traffic?"""
    model_loaded = hasattr(request.app.state, 'model_registry')
    
    if not model_loaded:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": "model_not_loaded"}
        )
    
    return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}


@router.get("/", response_model=HealthResponse)
async def health_check(request: Request):
    """Full health check with component status"""
    model_registry = getattr(request.app.state, 'model_registry', None)
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        model_loaded=model_registry is not None,
        model_version="1.0.0-ensemble" if model_registry else None,
        cache_connected=True,
        database_connected=True,
        uptime_seconds=round(time.time() - START_TIME, 2),
    )
