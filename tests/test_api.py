"""
Integration tests for Weather Forecast API
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def client():
    """Create test client with mocked dependencies"""
    with patch('app.services.model_registry.ModelRegistry.load_latest_model', new_callable=AsyncMock):
        from app.main import app
        with TestClient(app) as c:
            yield c


class TestHealthEndpoints:
    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Weather Forecast ML API"
        assert data["status"] == "operational"

    def test_liveness_probe(self, client):
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"

    def test_health_full(self, client):
        response = client.get("/health/")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "uptime_seconds" in data


class TestForecastEndpoints:
    def test_forecast_valid_request(self, client):
        payload = {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "days": 7,
            "units": "metric"
        }
        response = client.post("/api/v1/forecast/", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "forecast" in data
        assert len(data["forecast"]) == 7
        assert data["latitude"] == 40.7128
        assert "model_version" in data
        assert "processing_time_ms" in data

    def test_forecast_imperial_units(self, client):
        payload = {
            "latitude": 51.5074,
            "longitude": -0.1278,
            "days": 3,
            "units": "imperial"
        }
        response = client.post("/api/v1/forecast/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["units"] == "imperial"

    def test_forecast_invalid_latitude(self, client):
        payload = {
            "latitude": 200.0,  # Invalid
            "longitude": -74.0060,
            "days": 7,
        }
        response = client.post("/api/v1/forecast/", json=payload)
        assert response.status_code == 422

    def test_forecast_invalid_days(self, client):
        payload = {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "days": 100,  # Exceeds max of 14
        }
        response = client.post("/api/v1/forecast/", json=payload)
        assert response.status_code == 422

    def test_forecast_daily_structure(self, client):
        payload = {
            "latitude": 35.6762,
            "longitude": 139.6503,
            "days": 1,
        }
        response = client.post("/api/v1/forecast/", json=payload)
        assert response.status_code == 200

        day = response.json()["forecast"][0]
        required_fields = [
            "date", "day_of_week", "temperature_max", "temperature_min",
            "humidity", "precipitation_mm", "wind_speed_kmh", "condition",
            "confidence_score"
        ]
        for field in required_fields:
            assert field in day, f"Missing field: {field}"

    def test_forecast_by_city(self, client):
        response = client.get("/api/v1/forecast/locations/new_york?days=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["forecast"]) == 5

    def test_forecast_city_not_found(self, client):
        response = client.get("/api/v1/forecast/locations/unknowncity123")
        assert response.status_code == 404

    def test_confidence_scores_valid_range(self, client):
        payload = {"latitude": 48.8566, "longitude": 2.3522, "days": 7}
        response = client.post("/api/v1/forecast/", json=payload)
        assert response.status_code == 200

        for day in response.json()["forecast"]:
            assert 0.0 <= day["confidence_score"] <= 1.0

    def test_temperature_max_gt_min(self, client):
        payload = {"latitude": -33.8688, "longitude": 151.2093, "days": 7}
        response = client.post("/api/v1/forecast/", json=payload)
        assert response.status_code == 200

        for day in response.json()["forecast"]:
            assert day["temperature_max"] >= day["temperature_min"]

    def test_forecast_min_days(self, client):
        payload = {"latitude": 40.7128, "longitude": -74.0060, "days": 1}
        response = client.post("/api/v1/forecast/", json=payload)
        assert response.status_code == 200
        assert len(response.json()["forecast"]) == 1

    def test_forecast_max_days(self, client):
        payload = {"latitude": 40.7128, "longitude": -74.0060, "days": 14}
        response = client.post("/api/v1/forecast/", json=payload)
        assert response.status_code == 200
        assert len(response.json()["forecast"]) == 14

    def test_forecast_response_has_request_id(self, client):
        payload = {"latitude": 40.7128, "longitude": -74.0060, "days": 3}
        response = client.post("/api/v1/forecast/", json=payload)
        assert response.status_code == 200
        assert "request_id" in response.json()

    def test_forecast_response_has_data_sources(self, client):
        payload = {"latitude": 40.7128, "longitude": -74.0060, "days": 3}
        response = client.post("/api/v1/forecast/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "data_sources" in data
        assert isinstance(data["data_sources"], list)
        assert len(data["data_sources"]) > 0

    def test_forecast_humidity_valid_range(self, client):
        payload = {"latitude": 25.2048, "longitude": 55.2708, "days": 7}
        response = client.post("/api/v1/forecast/", json=payload)
        assert response.status_code == 200

        for day in response.json()["forecast"]:
            assert 0.0 <= day["humidity"] <= 100.0

    def test_forecast_precipitation_non_negative(self, client):
        payload = {"latitude": 1.3521, "longitude": 103.8198, "days": 7}
        response = client.post("/api/v1/forecast/", json=payload)
        assert response.status_code == 200

        for day in response.json()["forecast"]:
            assert day["precipitation_mm"] >= 0.0

    def test_forecast_processing_time_header(self, client):
        payload = {"latitude": 40.7128, "longitude": -74.0060, "days": 3}
        response = client.post("/api/v1/forecast/", json=payload)
        assert response.status_code == 200
        assert "X-Process-Time" in response.headers

    def test_forecast_missing_required_fields(self, client):
        # Missing longitude
        payload = {"latitude": 40.7128, "days": 7}
        response = client.post("/api/v1/forecast/", json=payload)
        assert response.status_code == 422

    def test_forecast_invalid_longitude(self, client):
        payload = {"latitude": 40.7128, "longitude": 999.0, "days": 7}
        response = client.post("/api/v1/forecast/", json=payload)
        assert response.status_code == 422


class TestModelEndpoints:
    def test_list_models(self, client):
        response = client.get("/api/v1/models/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0

    def test_current_model(self, client):
        response = client.get("/api/v1/models/current")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "accuracy" in data

    def test_trigger_retraining(self, client):
        payload = {
            "data_start_date": "2023-01-01",
            "data_end_date": "2023-12-31",
            "auto_deploy": False
        }
        response = client.post("/api/v1/models/retrain", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"

    def test_model_list_has_algorithm(self, client):
        response = client.get("/api/v1/models/")
        assert response.status_code == 200
        model = response.json()[0]
        assert "algorithm" in model

    def test_model_promote(self, client):
        response = client.post("/api/v1/models/1.0.0/promote?target_stage=Staging")
        assert response.status_code == 200
        data = response.json()
        assert data["promoted_to"] == "Staging"
        assert "promoted_at" in data


class TestAPIDocumentation:
    def test_openapi_schema(self, client):
        response = client.get("/openapi.json")
        assert response.status_code == 200

    def test_docs_available(self, client):
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_available(self, client):
        response = client.get("/redoc")
        assert response.status_code == 200
