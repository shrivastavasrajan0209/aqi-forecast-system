"""Realistic multi-city hourly AQI, weather, traffic, and seasonal data generator."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class CityProfile:
    id: str
    name: str
    country: str
    base_aqi: float
    seasonal_amp: float
    traffic_sensitivity: float
    wind_dispersion: float
    temp_base: float
    humidity_base: float
    seed: int


CITIES: dict[str, CityProfile] = {
    "delhi": CityProfile(
        id="delhi",
        name="New Delhi",
        country="India",
        base_aqi=155.0,
        seasonal_amp=55.0,
        traffic_sensitivity=38.0,
        wind_dispersion=4.2,
        temp_base=24.0,
        humidity_base=58.0,
        seed=101,
    ),
    "los-angeles": CityProfile(
        id="los-angeles",
        name="Los Angeles",
        country="USA",
        base_aqi=68.0,
        seasonal_amp=18.0,
        traffic_sensitivity=28.0,
        wind_dispersion=2.8,
        temp_base=21.0,
        humidity_base=52.0,
        seed=202,
    ),
    "london": CityProfile(
        id="london",
        name="London",
        country="UK",
        base_aqi=42.0,
        seasonal_amp=12.0,
        traffic_sensitivity=18.0,
        wind_dispersion=2.4,
        temp_base=13.0,
        humidity_base=74.0,
        seed=303,
    ),
    "beijing": CityProfile(
        id="beijing",
        name="Beijing",
        country="China",
        base_aqi=112.0,
        seasonal_amp=42.0,
        traffic_sensitivity=30.0,
        wind_dispersion=3.8,
        temp_base=15.0,
        humidity_base=49.0,
        seed=404,
    ),
    "bengaluru": CityProfile(
        id="bengaluru",
        name="Bengaluru",
        country="India",
        base_aqi=76.0,
        seasonal_amp=16.0,
        traffic_sensitivity=32.0,
        wind_dispersion=2.6,
        temp_base=23.5,
        humidity_base=64.0,
        seed=505,
    ),
}


def generate_city_history(city_id: str, hours: int = 24 * 60) -> pd.DataFrame:
    """Generate `hours` of hourly observations ending at the current hour."""
    if city_id not in CITIES:
        raise ValueError(f"Unknown city_id: {city_id}")

    profile = CITIES[city_id]
    rng = np.random.default_rng(profile.seed)

    end_time = datetime.now().replace(minute=0, second=0, microsecond=0)
    timestamps = [end_time - timedelta(hours=i) for i in range(hours - 1, -1, -1)]
    idx = np.arange(hours)

    hour_of_day = np.array([t.hour for t in timestamps], dtype=float)
    day_of_week = np.array([t.weekday() for t in timestamps], dtype=float)
    day_of_year = np.array([t.timetuple().tm_yday for t in timestamps], dtype=float)

    # Weather signals
    temp_diurnal = 5.5 * np.sin(2 * np.pi * (hour_of_day - 9) / 24.0)
    temp_seasonal = 7.0 * np.cos(2 * np.pi * (day_of_year - 172) / 365.0)
    temperature = profile.temp_base + temp_diurnal + temp_seasonal + rng.normal(0, 1.4, hours)

    humidity = np.clip(
        profile.humidity_base
        - 12.0 * np.sin(2 * np.pi * (hour_of_day - 9) / 24.0)
        + rng.normal(0, 5.0, hours),
        18.0,
        98.0,
    )

    wind_speed = np.clip(
        8.5 + 3.5 * np.sin(2 * np.pi * (hour_of_day - 11) / 24.0) + rng.normal(0, 2.4, hours),
        0.5,
        28.0,
    )
    pressure = 1013.0 + 4.5 * np.sin(2 * np.pi * idx / (24 * 5)) + rng.normal(0, 1.8, hours)
    precipitation = np.where(rng.random(hours) < 0.08, rng.exponential(2.5, hours), 0.0)

    # Traffic indicators: morning (8-10) and evening (17-20) peaks, lower on weekends
    is_weekend = (day_of_week >= 5).astype(float)
    morning_peak = np.exp(-0.5 * ((hour_of_day - 9.0) / 1.8) ** 2)
    evening_peak = np.exp(-0.5 * ((hour_of_day - 18.5) / 2.2) ** 2)
    traffic_index = np.clip(
        (0.25 + 0.65 * (morning_peak + 1.1 * evening_peak)) * (1.0 - 0.28 * is_weekend)
        + rng.normal(0, 0.05, hours),
        0.08,
        1.0,
    )

    # Seasonal trend
    seasonal_wave = profile.seasonal_amp * np.cos(2 * np.pi * (day_of_year - 15) / 365.0)

    # Autoregressive pollution dynamics
    aqi = np.zeros(hours, dtype=float)
    aqi[0] = profile.base_aqi + seasonal_wave[0]
    for t in range(1, hours):
        dispersion_effect = -profile.wind_dispersion * (wind_speed[t] - 8.0)
        washout_effect = -4.5 * precipitation[t]
        humidity_trap = 0.22 * (humidity[t] - 55.0)
        traffic_effect = profile.traffic_sensitivity * (traffic_index[t] - 0.45)
        target = (
            profile.base_aqi
            + seasonal_wave[t]
            + dispersion_effect
            + washout_effect
            + humidity_trap
            + traffic_effect
        )
        # Strong persistence + mean reversion + synoptic noise
        aqi[t] = np.clip(0.84 * aqi[t - 1] + 0.16 * target + rng.normal(0, 5.2), 12.0, 480.0)

    pm25 = np.clip(aqi * 0.42 + rng.normal(0, 3.0, hours), 4.0, 350.0)
    pm10 = np.clip(aqi * 0.78 + rng.normal(0, 5.5, hours), 8.0, 450.0)
    no2 = np.clip(18.0 + 45.0 * traffic_index + rng.normal(0, 4.0, hours), 5.0, 180.0)
    o3 = np.clip(
        28.0 + 1.1 * np.maximum(temperature - 15.0, 0.0) + rng.normal(0, 4.5, hours),
        8.0,
        160.0,
    )

    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "aqi": np.round(aqi, 1),
            "pm25": np.round(pm25, 1),
            "pm10": np.round(pm10, 1),
            "no2": np.round(no2, 1),
            "o3": np.round(o3, 1),
            "temperature": np.round(temperature, 1),
            "humidity": np.round(humidity, 1),
            "wind_speed": np.round(wind_speed, 1),
            "pressure": np.round(pressure, 1),
            "precipitation": np.round(precipitation, 2),
            "traffic_index": np.round(traffic_index, 3),
        }
    )
