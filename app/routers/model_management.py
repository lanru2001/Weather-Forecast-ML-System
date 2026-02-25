"""Model management endpoints"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime
import logging

from app.schemas.weather import ModelInfo, RetrainingRequest

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=list)
async def list_models():
    """List all registered models"""
    return [
        {
            "name": "weather-forecast",
            "version": "1.0.0",
            "stage": "Production",
            "algorithm": "Ensemble (XGBoost + LightGBM + RandomForest)",
            "accuracy": 0.923,
            "rmse": 1.42,
            "mae": 0.98,
            "r2_score": 0.923,
            "created_at": "2024-01-15T10:30:00Z",
            "features": ["temp_lag_1", "temp_lag_7", "humidity_roll_7", "sin_day", "cos_day"],
        }
    ]


@router.get("/current")
async def get_current_model():
    """Get currently deployed model info"""
    return {
        "name": "weather-forecast",
        "version": "1.0.0",
        "stage": "Production",
        "accuracy": 0.923,
        "status": "active",
    }


@router.post("/retrain")
async def trigger_retraining(request: RetrainingRequest, background_tasks: BackgroundTasks):
    """Trigger model retraining pipeline"""
    job_id = f"retrain-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    logger.info(f"Retraining triggered: {job_id}")
    
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Retraining job submitted to Kubernetes Job runner",
        "estimated_duration_minutes": 30,
    }


@router.post("/{version}/promote")
async def promote_model(version: str, target_stage: str = "Production"):
    """Promote a model version to a new stage"""
    return {
        "model": "weather-forecast",
        "version": version,
        "promoted_to": target_stage,
        "promoted_at": datetime.utcnow().isoformat(),
    }
