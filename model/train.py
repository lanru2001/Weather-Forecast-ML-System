"""
Weather Forecast ML Model Training Pipeline
Uses ensemble methods: XGBoost + LightGBM + Random Forest
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, VotingRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, TimeSeriesSplit, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
import xgboost as xgb
import lightgbm as lgb
import mlflow
import mlflow.sklearn
import mlflow.xgboost
import mlflow.lightgbm
import joblib
import json
import logging
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any, List
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class WeatherFeatureEngineer:
    """Feature engineering for weather data"""

    def __init__(self):
        self.scaler = StandardScaler()
        self.feature_names = []

    def create_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract time-based features"""
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])

        df['day_of_year'] = df['date'].dt.dayofyear
        df['day_of_week'] = df['date'].dt.dayofweek
        df['month'] = df['date'].dt.month
        df['quarter'] = df['date'].dt.quarter
        df['week_of_year'] = df['date'].dt.isocalendar().week.astype(int)
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)

        # Cyclical encoding for periodicity
        df['sin_day'] = np.sin(2 * np.pi * df['day_of_year'] / 365)
        df['cos_day'] = np.cos(2 * np.pi * df['day_of_year'] / 365)
        df['sin_month'] = np.sin(2 * np.pi * df['month'] / 12)
        df['cos_month'] = np.cos(2 * np.pi * df['month'] / 12)
        df['sin_dow'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['cos_dow'] = np.cos(2 * np.pi * df['day_of_week'] / 7)

        return df

    def create_lag_features(self, df: pd.DataFrame, cols: List[str], lags: List[int]) -> pd.DataFrame:
        """Create lagged features for time series"""
        df = df.copy()
        for col in cols:
            for lag in lags:
                df[f'{col}_lag_{lag}'] = df[col].shift(lag)
        return df

    def create_rolling_features(self, df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
        """Create rolling statistics"""
        df = df.copy()
        windows = [3, 7, 14]
        for col in cols:
            for window in windows:
                df[f'{col}_roll_mean_{window}'] = df[col].rolling(window).mean()
                df[f'{col}_roll_std_{window}'] = df[col].rolling(window).std()
                df[f'{col}_roll_max_{window}'] = df[col].rolling(window).max()
                df[f'{col}_roll_min_{window}'] = df[col].rolling(window).min()
        return df

    def create_weather_indices(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create derived weather indices"""
        df = df.copy()

        # Heat index approximation
        if 'temp_max' in df.columns and 'humidity' in df.columns:
            df['heat_index'] = (
                -8.78469475556 +
                1.61139411 * df['temp_max'] +
                2.33854883889 * df['humidity'] -
                0.14611605 * df['temp_max'] * df['humidity'] -
                0.012308094 * df['temp_max'] ** 2 -
                0.0164248277778 * df['humidity'] ** 2 +
                0.002211732 * df['temp_max'] ** 2 * df['humidity'] +
                0.00072546 * df['temp_max'] * df['humidity'] ** 2 -
                0.000003582 * df['temp_max'] ** 2 * df['humidity'] ** 2
            )

        # Temperature range
        if 'temp_max' in df.columns and 'temp_min' in df.columns:
            df['temp_range'] = df['temp_max'] - df['temp_min']
            df['temp_avg'] = (df['temp_max'] + df['temp_min']) / 2

        # Wind chill
        if 'temp_min' in df.columns and 'wind_speed' in df.columns:
            df['wind_chill'] = (
                13.12 + 0.6215 * df['temp_min'] -
                11.37 * df['wind_speed'] ** 0.16 +
                0.3965 * df['temp_min'] * df['wind_speed'] ** 0.16
            )

        return df

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Full feature engineering pipeline"""
        logger.info("Engineering features...")

        df = self.create_temporal_features(df)

        weather_cols = ['temp_max', 'temp_min', 'humidity', 'pressure', 'wind_speed', 'precipitation']
        existing_cols = [c for c in weather_cols if c in df.columns]

        df = self.create_lag_features(df, existing_cols, lags=[1, 2, 3, 7])
        df = self.create_rolling_features(df, existing_cols)
        df = self.create_weather_indices(df)

        df = df.dropna()
        logger.info(f"Feature engineering complete. Shape: {df.shape}")
        return df


class WeatherMLModel:
    """
    Ensemble ML model for weather forecasting
    Combines XGBoost, LightGBM, and Random Forest
    """

    def __init__(self, experiment_name: str = "weather-forecast"):
        self.experiment_name = experiment_name
        self.feature_engineer = WeatherFeatureEngineer()
        self.models = {}
        self.ensemble = None
        self.feature_columns = []
        self.target_columns = ['temp_max', 'temp_min', 'precipitation', 'humidity', 'wind_speed']
        self.model_metrics = {}

    def _build_xgboost(self) -> xgb.XGBRegressor:
        return xgb.XGBRegressor(
            n_estimators=500,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=3,
            gamma=0.1,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=42,
            n_jobs=-1,
            tree_method='hist',
        )

    def _build_lightgbm(self) -> lgb.LGBMRegressor:
        return lgb.LGBMRegressor(
            n_estimators=500,
            max_depth=6,
            learning_rate=0.05,
            num_leaves=31,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_samples=20,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=42,
            n_jobs=-1,
            verbose=-1,
        )

    def _build_random_forest(self) -> RandomForestRegressor:
        return RandomForestRegressor(
            n_estimators=200,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features='sqrt',
            random_state=42,
            n_jobs=-1,
        )

    def generate_synthetic_training_data(self, n_days: int = 3650) -> pd.DataFrame:
        """Generate synthetic weather data for demonstration"""
        logger.info(f"Generating {n_days} days of synthetic weather data...")
        np.random.seed(42)

        dates = pd.date_range(end=datetime.now(), periods=n_days, freq='D')
        n = len(dates)

        # Base seasonal patterns
        day_of_year = np.array([d.timetuple().tm_yday for d in dates])
        seasonal_temp = 15 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
        seasonal_precip = 3 + 2 * np.sin(2 * np.pi * (day_of_year - 30) / 365)

        data = {
            'date': dates,
            'temp_max': seasonal_temp + 20 + np.random.normal(0, 3, n),
            'temp_min': seasonal_temp + 10 + np.random.normal(0, 2, n),
            'humidity': np.clip(60 + seasonal_precip * 5 + np.random.normal(0, 10, n), 20, 100),
            'pressure': 1013 + np.random.normal(0, 8, n),
            'wind_speed': np.abs(15 + np.random.normal(0, 8, n)),
            'precipitation': np.abs(seasonal_precip + np.random.exponential(2, n)),
            'cloud_cover': np.clip(np.random.normal(50, 25, n), 0, 100),
            'latitude': np.full(n, 40.7128),
            'longitude': np.full(n, -74.0060),
        }

        df = pd.DataFrame(data)
        df['temp_max'] = df[['temp_max', 'temp_min']].max(axis=1)
        df['temp_min'] = df[['temp_max', 'temp_min']].min(axis=1)
        df['precipitation'] = np.where(df['precipitation'] < 1, 0, df['precipitation'])

        return df

    def prepare_features(self, df: pd.DataFrame, target: str) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare features and target for training"""
        df_engineered = self.feature_engineer.engineer_features(df)

        exclude_cols = ['date'] + self.target_columns + [
            c for c in self.target_columns if c != target and c in df_engineered.columns
        ]
        feature_cols = [c for c in df_engineered.columns if c not in exclude_cols]

        # Keep only numeric columns
        feature_cols = [c for c in feature_cols if df_engineered[c].dtype in ['float64', 'int64', 'int32']]

        X = df_engineered[feature_cols].copy()
        y = df_engineered[target].copy()

        self.feature_columns = feature_cols
        return X, y

    def train(self, df: pd.DataFrame = None) -> Dict[str, Any]:
        """Train the ensemble model with MLflow tracking"""

        if df is None:
            df = self.generate_synthetic_training_data()

        mlflow.set_experiment(self.experiment_name)

        with mlflow.start_run(run_name=f"weather-ensemble-{datetime.now().strftime('%Y%m%d-%H%M%S')}") as run:
            logger.info("🏋️ Starting model training with MLflow tracking...")

            mlflow.log_param("n_samples", len(df))
            mlflow.log_param("date_range", f"{df['date'].min()} to {df['date'].max()}")
            mlflow.log_param("targets", self.target_columns)

            all_metrics = {}

            for target in self.target_columns:
                logger.info(f"Training model for target: {target}")

                X, y = self.prepare_features(df, target)

                # Time-series split
                tss = TimeSeriesSplit(n_splits=5)
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, shuffle=False
                )

                # Build models
                xgb_model = self._build_xgboost()
                lgb_model = self._build_lightgbm()
                rf_model = self._build_random_forest()

                # Ensemble
                ensemble = VotingRegressor(
                    estimators=[
                        ('xgb', xgb_model),
                        ('lgb', lgb_model),
                        ('rf', rf_model),
                    ],
                    weights=[0.4, 0.4, 0.2],
                )

                ensemble.fit(X_train, y_train)
                y_pred = ensemble.predict(X_test)

                # Metrics
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                mae = mean_absolute_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)

                metrics = {"rmse": rmse, "mae": mae, "r2": r2}
                all_metrics[target] = metrics

                mlflow.log_metrics({
                    f"{target}_rmse": rmse,
                    f"{target}_mae": mae,
                    f"{target}_r2": r2,
                })

                logger.info(f"  {target}: RMSE={rmse:.3f}, MAE={mae:.3f}, R²={r2:.3f}")

                self.models[target] = ensemble

            # Log average metrics
            avg_r2 = np.mean([m['r2'] for m in all_metrics.values()])
            avg_rmse = np.mean([m['rmse'] for m in all_metrics.values()])
            mlflow.log_metric("avg_r2", avg_r2)
            mlflow.log_metric("avg_rmse", avg_rmse)
            mlflow.log_param("feature_count", len(self.feature_columns))

            # Save model
            model_path = f"/tmp/weather_model_{run.info.run_id}"
            joblib.dump({
                'models': self.models,
                'feature_columns': self.feature_columns,
                'feature_engineer': self.feature_engineer,
                'metrics': all_metrics,
                'run_id': run.info.run_id,
                'trained_at': datetime.now().isoformat(),
            }, model_path + '.pkl')

            mlflow.log_artifact(model_path + '.pkl', "model")

            self.model_metrics = all_metrics
            self.run_id = run.info.run_id

            logger.info(f"✅ Training complete! Average R²: {avg_r2:.4f}")
            return {
                "run_id": run.info.run_id,
                "metrics": all_metrics,
                "avg_r2": avg_r2,
                "avg_rmse": avg_rmse,
                "model_path": model_path + '.pkl',
            }

    def predict(self, features: Dict[str, Any], forecast_days: int = 7) -> List[Dict]:
        """Generate multi-day forecast"""
        if not self.models:
            raise ValueError("Model not trained. Call train() first.")

        forecasts = []
        current_data = pd.DataFrame([features])
        current_data['date'] = pd.to_datetime(current_data.get('date', datetime.now()))

        for day in range(forecast_days):
            forecast_date = current_data['date'].iloc[-1] + timedelta(days=1)
            current_data_copy = current_data.copy()
            current_data_copy['date'] = forecast_date

            df_features = self.feature_engineer.engineer_features(current_data_copy)
            available_features = [f for f in self.feature_columns if f in df_features.columns]

            X_pred = df_features[available_features].iloc[-1:]

            day_forecast = {'date': forecast_date.strftime('%Y-%m-%d')}

            for target in self.target_columns:
                if target in self.models:
                    # Pad missing features with zeros
                    X_padded = pd.DataFrame(0, index=X_pred.index, columns=self.feature_columns)
                    for col in available_features:
                        X_padded[col] = X_pred[col].values

                    pred = self.models[target].predict(X_padded)[0]
                    day_forecast[target] = round(float(pred), 2)

            forecasts.append(day_forecast)

            # Update current data with prediction for next iteration
            new_row = current_data.iloc[-1].copy()
            new_row['date'] = forecast_date
            for target in self.target_columns:
                if target in day_forecast:
                    new_row[target] = day_forecast[target]
            current_data = pd.concat([current_data, pd.DataFrame([new_row])], ignore_index=True)

        return forecasts


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("🌤️ Weather ML Model Training")
    print("=" * 50)

    model = WeatherMLModel()
    results = model.train()

    print(f"\n✅ Training Complete!")
    print(f"Run ID: {results['run_id']}")
    print(f"Average R²: {results['avg_r2']:.4f}")
    print(f"Average RMSE: {results['avg_rmse']:.4f}")
    print(f"Model saved to: {results['model_path']}")
