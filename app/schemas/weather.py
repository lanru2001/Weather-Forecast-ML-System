"""Pydantic schemas for request/response validation"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class WeatherCondition(str, Enum):
    SUNNY = "Sunny"
    CLOUDY = "Cloudy"
    RAINY = "Rainy"
    SNOWY = "Snowy"
    STORMY = "Stormy"
    FOGGY = "Foggy"
    WINDY = "Windy"
    PARTLY_CLOUDY = "Partly Cloudy"


class ForecastRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude (-90 to 90)")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude (-180 to 180)")
    days: int = Field(default=7, ge=1, le=14, description="Number of days to forecast")
    include_hourly: bool = Field(default=False, description="Include hourly breakdown")
    units: str = Field(default="metric", description="Units: metric or imperial")

    class Config:
        json_schema_extra = {
            "example": {
                "latitude": 40.7128,
                "longitude": -74.0060,
                "days": 7,
                "include_hourly": False,
                "units": "metric"
            }
        }


class HourlyForecast(BaseModel):
    hour: int
    temperature: float
    feels_like: float
    humidity: float
    precipitation_probability: float
    wind_speed: float
    condition: WeatherCondition


class DailyForecast(BaseModel):
    date: str
    day_of_week: str
    temperature_max: float = Field(..., description="Max temperature")
    temperature_min: float = Field(..., description="Min temperature")
    temperature_avg: float = Field(..., description="Average temperature")
    feels_like_max: float
    feels_like_min: float
    humidity: float = Field(..., ge=0, le=100, description="Humidity percentage")
    precipitation_mm: float = Field(..., ge=0, description="Precipitation in mm")
    precipitation_probability: float = Field(..., ge=0, le=100)
    wind_speed_kmh: float = Field(..., ge=0)
    wind_direction: str
    wind_gust_kmh: float
    pressure_hpa: float
    uv_index: float = Field(..., ge=0, le=11)
    visibility_km: float
    cloud_cover: float = Field(..., ge=0, le=100)
    sunrise: str
    sunset: str
    condition: WeatherCondition
    condition_description: str
    confidence_score: float = Field(..., ge=0, le=1, description="Model confidence")
    hourly: Optional[List[HourlyForecast]] = None


class LocationInfo(BaseModel):
    city: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    timezone: str
    elevation_m: Optional[float] = None


class ForecastResponse(BaseModel):
    request_id: str
    latitude: float
    longitude: float
    location: LocationInfo
    units: str
    generated_at: datetime
    model_version: str
    model_accuracy: float
    forecast: List[DailyForecast]
    data_sources: List[str]
    processing_time_ms: float


class HistoricalWeatherInput(BaseModel):
    """Input features for batch prediction"""
    date: str
    latitude: float
    longitude: float
    temp_max: float
    temp_min: float
    humidity: float
    pressure: float
    wind_speed: float
    cloud_cover: float
    precipitation: float


class ModelInfo(BaseModel):
    name: str
    version: str
    stage: str
    accuracy: float
    rmse: float
    mae: float
    r2_score: float
    created_at: datetime
    features: List[str]
    algorithm: str


class RetrainingRequest(BaseModel):
    data_start_date: str
    data_end_date: str
    model_params: Optional[Dict[str, Any]] = None
    auto_deploy: bool = False


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    model_loaded: bool
    model_version: Optional[str]
    cache_connected: bool
    database_connected: bool
    uptime_seconds: float
