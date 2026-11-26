
"""Open-Meteo integration for real-time model-based AQI data."""

from __future__ import annotations

import ssl
from datetime import datetime
from typing import Any

import httpx
import truststore

# Use Windows' trusted certificate store.
truststore.inject_into_ssl()


AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

CITIES = {
    "delhi": {
        "id": "delhi",
        "name": "New Delhi",
        "country": "India",
        "latitude": 28.6139,
        "longitude": 77.2090,
    },
    "los-angeles": {
        "id": "los-angeles",
        "name": "Los Angeles",
        "country": "USA",
        "latitude": 34.0522,
        "longitude": -118.2437,
    },
    "london": {
        "id": "london",
        "name": "London",
        "country": "UK",
        "latitude": 51.5072,
        "longitude": -0.1276,
    },
    "beijing": {
        "id": "beijing",
        "name": "Beijing",
        "country": "China",
        "latitude": 39.9042,
        "longitude": 116.4074,
    },
    "bengaluru": {
        "id": "bengaluru",
        "name": "Bengaluru",
        "country": "India",
        "latitude": 12.9716,
        "longitude": 77.5946,
    },
}


def _number(value: Any) -> float | None:
    """Convert an API value to a float, preserving missing values."""
    if value is None:
        return None
    return round(float(value), 2)


def fetch_city_data(city_id: str, horizon: int = 72) -> dict:
    """Fetch current conditions, recent hourly history and AQI forecast."""

    if city_id not in CITIES:
        raise ValueError(f"Unknown city: {city_id}")

    if horizon < 24 or horizon > 72:
        raise ValueError("Forecast horizon must be between 24 and 72 hours.")

    city = CITIES[city_id]

    air_params = {
        "latitude": city["latitude"],
        "longitude": city["longitude"],
        "current": (
            "us_aqi,pm2_5,pm10,nitrogen_dioxide,"
            "ozone,carbon_monoxide,sulphur_dioxide"
        ),
        "hourly": (
            "us_aqi,pm2_5,pm10,nitrogen_dioxide,"
            "ozone,carbon_monoxide,sulphur_dioxide"
        ),
        "past_hours": 24,
        "forecast_hours": horizon + 1,
        "timezone": "auto",
    }

    weather_params = {
        "latitude": city["latitude"],
        "longitude": city["longitude"],
        "current": (
            "temperature_2m,relative_humidity_2m,wind_speed_10m"
        ),
        "hourly": (
            "temperature_2m,relative_humidity_2m,wind_speed_10m"
        ),
        "past_hours": 24,
        "forecast_hours": horizon + 1,
        "timezone": "auto",
    }

    # Explicitly use Windows' certificate store.
    ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

    with httpx.Client(
        timeout=30.0,
        verify=ssl_context,
        follow_redirects=True,
    ) as client:

        air_response = client.get(
            AIR_QUALITY_URL,
            params=air_params,
        )
        air_response.raise_for_status()
        air = air_response.json()

        weather_response = client.get(
            WEATHER_URL,
            params=weather_params,
        )
        weather_response.raise_for_status()
        weather = weather_response.json()

    air_current = air.get("current") or {}
    weather_current = weather.get("current") or {}
    air_hourly = air.get("hourly") or {}
    weather_hourly = weather.get("hourly") or {}

    if air_current.get("us_aqi") is None:
        raise RuntimeError(
            "Open-Meteo did not return current US AQI data."
        )

    if not air_current.get("time"):
        raise RuntimeError(
            "Open-Meteo did not return a current AQI timestamp."
        )

    air_times = air_hourly.get("time", [])
    weather_times = weather_hourly.get("time", [])

    air_index = {
        timestamp: index
        for index, timestamp in enumerate(air_times)
    }

    weather_index = {
        timestamp: index
        for index, timestamp in enumerate(weather_times)
    }

    def hourly_value(
        data: dict,
        key: str,
        index: dict,
        timestamp: str,
    ) -> float | None:

        position = index.get(timestamp)
        values = data.get(key, [])

        if position is None or position >= len(values):
            return None

        return _number(values[position])

    current_time = datetime.fromisoformat(
        air_current["time"]
    )

    common_times = sorted(
        set(air_times).intersection(weather_times)
    )

    history = []
    future = []

    for timestamp in common_times:
        time_value = datetime.fromisoformat(timestamp)

        aqi = hourly_value(
            air_hourly,
            "us_aqi",
            air_index,
            timestamp,
        )

        if aqi is None:
            continue

        record = {
            "timestamp": timestamp,
            "aqi": aqi,
            "pm25": hourly_value(
                air_hourly, "pm2_5", air_index, timestamp
            ),
            "pm10": hourly_value(
                air_hourly, "pm10", air_index, timestamp
            ),
            "temperature": hourly_value(
                weather_hourly,
                "temperature_2m",
                weather_index,
                timestamp,
            ),
            "humidity": hourly_value(
                weather_hourly,
                "relative_humidity_2m",
                weather_index,
                timestamp,
            ),
            "wind_speed": hourly_value(
                weather_hourly,
                "wind_speed_10m",
                weather_index,
                timestamp,
            ),
            "traffic_index": None,
        }

        if time_value <= current_time:
            history.append(record)
        else:
            future.append(record)

    history = history[-24:]
    future = future[:horizon]

    if not history:
        raise RuntimeError(
            "Open-Meteo returned no recent AQI history."
        )

    if len(future) < horizon:
        raise RuntimeError(
            f"Open-Meteo returned only {len(future)} forecast hours; "
            f"{horizon} were requested."
        )

    forecast = []

    for index, record in enumerate(future, start=1):
        forecast.append({
            "horizon_hour": index,
            "timestamp": record["timestamp"],
            "predicted_aqi": record["aqi"],
            "pm25": record["pm25"],
            "pm10": record["pm10"],
            "temperature": record["temperature"],
            "humidity": record["humidity"],
            "wind_speed": record["wind_speed"],
            "traffic_index": None,
        })

    current = {
        "aqi": int(air_current["us_aqi"]),
        "pm25": _number(air_current.get("pm2_5")),
        "pm10": _number(air_current.get("pm10")),
        "no2": _number(air_current.get("nitrogen_dioxide")),
        "ozone": _number(air_current.get("ozone")),
        "co": _number(air_current.get("carbon_monoxide")),
        "so2": _number(air_current.get("sulphur_dioxide")),
        "temperature": _number(
            weather_current.get("temperature_2m")
        ),
        "humidity": _number(
            weather_current.get("relative_humidity_2m")
        ),
        "wind_speed": _number(
            weather_current.get("wind_speed_10m")
        ),
        "traffic_index": None,
    }

    return {
        "city": {
            "id": city["id"],
            "name": city["name"],
            "country": city["country"],
        },
        "current": current,
        "recent_history": history,
        "forecast": forecast,
        "source": "Open-Meteo Air Quality API",
        "source_type": (
            "Atmospheric model estimates, "
            "not ground-station measurements"
        ),
        "timezone": air.get("timezone"),
        "updated_at": air_current.get("time"),
    }
