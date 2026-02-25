"""Application configuration using Pydantic Settings"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # API Settings
    APP_NAME: str = "Weather Forecast ML API"
    DEBUG: bool = False
    WORKERS: int = 4
    ALLOWED_ORIGINS: List[str] = ["*"]

    # Database
    DATABASE_URL: str = "postgresql://weather:weather123@localhost:5432/weatherdb"
    REDIS_URL: str = "redis://localhost:6379/0"

    # ML Model Settings
    MODEL_PATH: str = "/models"
    MODEL_REGISTRY_URI: str = "http://mlflow:5000"
    MODEL_NAME: str = "weather-forecast"
    MODEL_STAGE: str = "Production"
    FEATURE_STORE_URI: str = "http://feast:6566"

    # Monitoring
    PROMETHEUS_PORT: int = 9090
    ENABLE_METRICS: bool = True
    JAEGER_HOST: str = "jaeger"
    JAEGER_PORT: int = 6831

    # External APIs
    OPENWEATHER_API_KEY: Optional[str] = None
    WEATHER_DATA_SOURCE: str = "openweathermap"

    # Cache Settings
    CACHE_TTL: int = 3600  # 1 hour
    PREDICTION_CACHE_TTL: int = 1800  # 30 minutes

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    KAFKA_WEATHER_TOPIC: str = "weather-data"
    KAFKA_PREDICTIONS_TOPIC: str = "weather-predictions"

    # AWS Settings (for S3 model artifacts)
    AWS_REGION: str = "us-east-1"
    S3_BUCKET: str = "weather-ml-artifacts"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
