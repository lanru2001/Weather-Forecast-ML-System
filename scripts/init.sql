-- ============================================================
-- Weather ML Database Initialization
-- ============================================================

-- Create MLflow database
CREATE DATABASE mlflowdb;

-- Weather observations table
CREATE TABLE IF NOT EXISTS weather_observations (
    id               BIGSERIAL PRIMARY KEY,
    latitude         DECIMAL(8, 5)            NOT NULL,
    longitude        DECIMAL(8, 5)            NOT NULL,
    observed_at      TIMESTAMP WITH TIME ZONE NOT NULL,
    temp_max         DECIMAL(6, 2),
    temp_min         DECIMAL(6, 2),
    humidity         DECIMAL(5, 2),
    pressure_hpa     DECIMAL(7, 2),
    wind_speed_kmh   DECIMAL(6, 2),
    precipitation_mm DECIMAL(6, 2),
    cloud_cover      DECIMAL(5, 2),
    condition        VARCHAR(50),
    source           VARCHAR(50)              NOT NULL DEFAULT 'openweathermap',
    created_at       TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_observations_location ON weather_observations (latitude, longitude);
CREATE INDEX idx_observations_time     ON weather_observations (observed_at DESC);

-- Predictions log table
CREATE TABLE IF NOT EXISTS prediction_logs (
    id              BIGSERIAL PRIMARY KEY,
    request_id      UUID                     NOT NULL UNIQUE,
    latitude        DECIMAL(8, 5)            NOT NULL,
    longitude       DECIMAL(8, 5)            NOT NULL,
    forecast_days   INTEGER                  NOT NULL,
    model_version   VARCHAR(50)              NOT NULL,
    prediction_data JSONB                    NOT NULL,
    processing_ms   DECIMAL(8, 2),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_predictions_request ON prediction_logs (request_id);
CREATE INDEX idx_predictions_created ON prediction_logs (created_at DESC);

-- Model metrics tracking
CREATE TABLE IF NOT EXISTS model_metrics (
    id           BIGSERIAL PRIMARY KEY,
    run_id       VARCHAR(100)             NOT NULL UNIQUE,
    model_name   VARCHAR(100)             NOT NULL,
    version      VARCHAR(50),
    stage        VARCHAR(20)              DEFAULT 'Staging',
    rmse         DECIMAL(10, 4),
    mae          DECIMAL(10, 4),
    r2_score     DECIMAL(10, 4),
    metrics_json JSONB,
    trained_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deployed_at  TIMESTAMP WITH TIME ZONE
);

-- Data drift monitoring
CREATE TABLE IF NOT EXISTS drift_reports (
    id           BIGSERIAL PRIMARY KEY,
    report_date  DATE                     NOT NULL,
    feature_name VARCHAR(100)             NOT NULL,
    drift_score  DECIMAL(8, 4),
    is_drifted   BOOLEAN                  DEFAULT FALSE,
    threshold    DECIMAL(8, 4)            DEFAULT 0.1,
    created_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES    IN SCHEMA public TO weather;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO weather;
