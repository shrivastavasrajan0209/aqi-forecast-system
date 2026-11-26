
"""AQI integration using Open-Meteo and weather using WeatherAPI.com."""

from __future__ import annotations

import copy
import os
import ssl
import time
from datetime import datetime
from threading import Lock
from typing import Any

import httpx
import truststore

truststore.inject_into_ssl()

AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
WEATHER_URL = "https://api.weatherapi.com/v1/forecast.json"

CACHE_TTL = 15 * 60
WEATHER_RETRY_COOLDOWN = 5 * 60

_cache: dict[tuple[str, int], dict[str, Any]] = {}
_cache_lock = Lock()

_weather_cache: dict[str, Any] = {
    "data": {},
    "saved_at": 0,
}
_weather_retry_after: float = 0
_weather_lock = Lock()

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
    if value is None:
        return None
    return round(float(value), 2)


def _get_cached(
    key: tuple[str, int],
) -> tuple[dict | None, dict | None]:
    """Return fresh and stale AQI results."""

    with _cache_lock:
        entry = _cache.get(key)

        if not entry:
            return None, None

        result = copy.deepcopy(entry["data"])

        if time.time() - entry["saved_at"] < CACHE_TTL:
            return result, result

        return None, result


def _save_cache(key: tuple[str, int], result: dict) -> None:
    with _cache_lock:
        _cache[key] = {
            "data": copy.deepcopy(result),
            "saved_at": time.time(),
        }


def _get_weather_batch() -> dict[str, dict[str, Any]]:
    """
    Fetch weather for all five cities using WeatherAPI.com.

    One shared cache is used for all forecast horizons.
    """

    global _weather_retry_after

    api_key = os.getenv("WEATHERAPI_KEY")

    if not api_key:
        print("Weather unavailable: WEATHERAPI_KEY is not configured.")
        return {}

    now = time.time()

    with _weather_lock:
        cached = copy.deepcopy(_weather_cache["data"])

        if (
            cached
            and now - _weather_cache["saved_at"] < CACHE_TTL
        ):
            return cached

        if now < _weather_retry_after:
            if cached:
                print("Weather cooldown active. Using cached data.")
            return cached

        weather_by_city = {}

        params_base = {
            "key": api_key,
            "days": 3,
            "aqi": "no",
            "alerts": "no",
        }

        ssl_context = truststore.SSLContext(
            ssl.PROTOCOL_TLS_CLIENT
        )

        try:
            with httpx.Client(
                timeout=30.0,
                verify=ssl_context,
                follow_redirects=True,
            ) as client:

                for city_id, city in CITIES.items():
                    params = {
                        **params_base,
                        "q": (
                            f'{city["latitude"]},'
                            f'{city["longitude"]}'
                        ),
                    }

                    try:
                        response = client.get(
                            WEATHER_URL,
                            params=params,
                        )
                        response.raise_for_status()
                        payload = response.json()

                        current = payload.get("current") or {}
                        forecast = payload.get("forecast") or {}

                        forecast_days = (
                            forecast.get("forecastday") or []
                        )

                        if not current or not forecast_days:
                            raise ValueError(
                                "WeatherAPI returned incomplete data."
                            )

                        hourly = {}

                        for day in forecast_days:
                            for hour in day.get("hour", []):
                                timestamp = hour.get("time")

                                if timestamp:
                                    # Normalize to the AQI timestamp format.
                                    normalized = (
                                        timestamp.replace(" ", "T")[:16]
                                    )
                                    hourly[normalized] = {
                                        "temperature_2m": hour.get(
                                            "temp_c"
                                        ),
                                        "relative_humidity_2m": hour.get(
                                            "humidity"
                                        ),
                                        "wind_speed_10m": hour.get(
                                            "wind_kph"
                                        ),
                                    }

                        weather_by_city[city_id] = {
                            "current": {
                                "temperature_2m": current.get("temp_c"),
                                "relative_humidity_2m": current.get(
                                    "humidity"
                                ),
                                "wind_speed_10m": current.get("wind_kph"),
                            },
                            "hourly": hourly,
                        }

                        print(
                            f"Weather updated successfully: {city_id}"
                        )

                    except (
                        httpx.HTTPError,
                        ValueError,
                        KeyError,
                    ) as error:
                        print(
                            f"Weather unavailable for {city_id}: {error}"
                        )

            if weather_by_city:
                # Preserve previously successful city data if one
                # city temporarily fails.
                combined = {
                    **cached,
                    **weather_by_city,
                }

                _weather_cache["data"] = copy.deepcopy(combined)
                _weather_cache["saved_at"] = time.time()

                _weather_retry_after = 0

                print(
                    "Weather cache updated for "
                    f"{len(weather_by_city)} cities."
                )

                return combined

            _weather_retry_after = (
                time.time() + WEATHER_RETRY_COOLDOWN
            )

            print("Weather provider returned no usable city data.")

            return cached

        except (httpx.HTTPError, ValueError) as error:
            _weather_retry_after = (
                time.time() + WEATHER_RETRY_COOLDOWN
            )

            print(f"Weather service unavailable: {error}")

            return cached


def _weather_value(
    hourly: dict,
    key: str,
    timestamp: str,
) -> float | None:
    normalized = timestamp.replace(" ", "T")[:16]
    record = hourly.get(normalized)

    if not record:
        return None

    return _number(record.get(key))


def _add_weather(
    result: dict,
    weather: dict[str, Any] | None,
) -> None:
    """Add weather data to the AQI response."""

    if not weather:
        return

    current = weather.get("current") or {}
    hourly = weather.get("hourly") or {}

    result["current"]["temperature"] = _number(
        current.get("temperature_2m")
    )
    result["current"]["humidity"] = _number(
        current.get("relative_humidity_2m")
    )
    result["current"]["wind_speed"] = _number(
        current.get("wind_speed_10m")
    )

    # WeatherAPI free forecast does not provide past hourly data
    # beyond its available forecast response.
    for record in result["recent_history"]:
        record["temperature"] = None
        record["humidity"] = None
        record["wind_speed"] = None

    for record in result["forecast"]:
        timestamp = record["timestamp"]

        record["temperature"] = _weather_value(
            hourly, "temperature_2m", timestamp
        )
        record["humidity"] = _weather_value(
            hourly, "relative_humidity_2m", timestamp
        )
        record["wind_speed"] = _weather_value(
            hourly, "wind_speed_10m", timestamp
        )


def fetch_city_data(city_id: str, horizon: int = 72) -> dict:
    """Fetch AQI data and enrich it with WeatherAPI weather."""

    if city_id not in CITIES:
        raise ValueError(f"Unknown city: {city_id}")

    if horizon < 24 or horizon > 72:
        raise ValueError(
            "Forecast horizon must be between 24 and 72 hours."
        )

    cache_key = (city_id, horizon)
    fresh_cache, stale_cache = _get_cached(cache_key)

    if fresh_cache is not None:
        if fresh_cache["current"].get("temperature") is None:
            weather_batch = _get_weather_batch()
            _add_weather(
                fresh_cache,
                weather_batch.get(city_id),
            )
            _save_cache(cache_key, fresh_cache)

        return fresh_cache

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

    ssl_context = truststore.SSLContext(
        ssl.PROTOCOL_TLS_CLIENT
    )

    try:
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

    except httpx.HTTPError as error:
        if stale_cache is not None:
            print(
                f"AQI API unavailable for {city_id}; "
                "using previously cached forecast."
            )
            return stale_cache

        raise RuntimeError(
            f"Unable to retrieve AQI data from Open-Meteo: {error}"
        ) from error

    air_current = air.get("current") or {}
    air_hourly = air.get("hourly") or {}

    if air_current.get("us_aqi") is None:
        raise RuntimeError(
            "Open-Meteo did not return current US AQI data."
        )

    if not air_current.get("time"):
        raise RuntimeError(
            "Open-Meteo did not return a current AQI timestamp."
        )

    air_times = air_hourly.get("time") or []

    air_index = {
        timestamp: index
        for index, timestamp in enumerate(air_times)
    }

    def aqi_value(key: str, timestamp: str) -> float | None:
        position = air_index.get(timestamp)
        values = air_hourly.get(key) or []

        if position is None or position >= len(values):
            return None

        return _number(values[position])

    current_time = datetime.fromisoformat(
        air_current["time"]
    )

    history = []
    future = []

    for timestamp in sorted(air_times):
        time_value = datetime.fromisoformat(timestamp)
        aqi = aqi_value("us_aqi", timestamp)

        if aqi is None:
            continue

        record = {
            "timestamp": timestamp,
            "aqi": aqi,
            "pm25": aqi_value("pm2_5", timestamp),
            "pm10": aqi_value("pm10", timestamp),
            "temperature": None,
            "humidity": None,
            "wind_speed": None,
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
            "temperature": None,
            "humidity": None,
            "wind_speed": None,
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
        "temperature": None,
        "humidity": None,
        "wind_speed": None,
        "traffic_index": None,
    }

    result = {
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

    weather_batch = _get_weather_batch()
    _add_weather(result, weather_batch.get(city_id))

    _save_cache(cache_key, result)

    return result
