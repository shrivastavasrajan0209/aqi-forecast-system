"""Feature engineering from weather, seasonal trends, traffic, and pollution history."""

from __future__ import annotations

import numpy as np
import pandas as pd

FEATURE_GROUPS: dict[str, str] = {
    "aqi_lag_1": "Pollution History",
    "aqi_lag_3": "Pollution History",
    "aqi_lag_6": "Pollution History",
    "aqi_lag_12": "Pollution History",
    "aqi_lag_24": "Pollution History",
    "aqi_roll_mean_6": "Pollution History",
    "aqi_roll_std_6": "Pollution History",
    "aqi_roll_mean_24": "Pollution History",
    "pm25_lag_1": "Pollution History",
    "no2_lag_1": "Pollution History",
    "temperature": "Weather",
    "humidity": "Weather",
    "wind_speed": "Weather",
    "pressure": "Weather",
    "precipitation": "Weather",
    "stagnation_index": "Weather",
    "traffic_index": "Traffic Indicators",
    "is_rush_hour": "Traffic Indicators",
    "traffic_x_stagnation": "Traffic Indicators",
    "hour_sin": "Seasonal & Cyclical",
    "hour_cos": "Seasonal & Cyclical",
    "dow_sin": "Seasonal & Cyclical",
    "dow_cos": "Seasonal & Cyclical",
    "is_weekend": "Seasonal & Cyclical",
}

FEATURE_LABELS: dict[str, str] = {
    "aqi_lag_1": "AQI (1h ago)",
    "aqi_lag_3": "AQI (3h ago)",
    "aqi_lag_6": "AQI (6h ago)",
    "aqi_lag_12": "AQI (12h ago)",
    "aqi_lag_24": "AQI (24h ago)",
    "aqi_roll_mean_6": "6h Rolling Mean AQI",
    "aqi_roll_std_6": "6h AQI Volatility",
    "aqi_roll_mean_24": "24h Rolling Mean AQI",
    "pm25_lag_1": "PM2.5 (1h ago)",
    "no2_lag_1": "NO₂ (1h ago)",
    "temperature": "Temperature (°C)",
    "humidity": "Relative Humidity (%)",
    "wind_speed": "Wind Speed (km/h)",
    "pressure": "Barometric Pressure (hPa)",
    "precipitation": "Precipitation (mm)",
    "stagnation_index": "Air Stagnation Index",
    "traffic_index": "Traffic Congestion Index",
    "is_rush_hour": "Rush Hour Flag",
    "traffic_x_stagnation": "Traffic × Stagnation",
    "hour_sin": "Time of Day (sin)",
    "hour_cos": "Time of Day (cos)",
    "dow_sin": "Day of Week (sin)",
    "dow_cos": "Day of Week (cos)",
    "is_weekend": "Weekend Flag",
}


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create supervised ML features from raw hourly observations."""
    feat = df.copy()
    ts = pd.to_datetime(feat["timestamp"])

    # Pollution history lags and rolling statistics
    for lag in (1, 3, 6, 12, 24):
        feat[f"aqi_lag_{lag}"] = feat["aqi"].shift(lag)
    feat["aqi_roll_mean_6"] = feat["aqi"].shift(1).rolling(6).mean()
    feat["aqi_roll_std_6"] = feat["aqi"].shift(1).rolling(6).std().fillna(0.0)
    feat["aqi_roll_mean_24"] = feat["aqi"].shift(1).rolling(24).mean()
    feat["pm25_lag_1"] = feat["pm25"].shift(1)
    feat["no2_lag_1"] = feat["no2"].shift(1)

    # Weather derived features
    feat["stagnation_index"] = feat["humidity"] / (feat["wind_speed"] + 1.0)

    # Traffic indicators
    hour = ts.dt.hour
    dow = ts.dt.dayofweek
    feat["is_rush_hour"] = (((hour >= 7) & (hour <= 10)) | ((hour >= 17) & (hour <= 20))).astype(float)
    feat["traffic_x_stagnation"] = feat["traffic_index"] * feat["stagnation_index"]

    # Seasonal & cyclical encodings
    feat["hour_sin"] = np.sin(2 * np.pi * hour / 24.0)
    feat["hour_cos"] = np.cos(2 * np.pi * hour / 24.0)
    feat["dow_sin"] = np.sin(2 * np.pi * dow / 7.0)
    feat["dow_cos"] = np.cos(2 * np.pi * dow / 7.0)
    feat["is_weekend"] = (dow >= 5).astype(float)

    return feat


FEATURE_COLUMNS = list(FEATURE_GROUPS.keys())
