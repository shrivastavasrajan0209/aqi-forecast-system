
"""FastAPI application for the AeroPulse AQI forecasting dashboard."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .open_meteo import CITIES, fetch_city_data
from .health_advisor import generate_health_guidance, get_aqi_category

app = FastAPI(
    title="AeroPulse AQI Forecast API",
    description=(
        "24-72 hour AQI forecasts and rule-based health guidance "
        "using Open-Meteo atmospheric model estimates."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check() -> dict:
    return {
        "status": "ok",
        "data_source": "Open-Meteo",
        "forecast_type": "Atmospheric model estimates",
    }


@app.get("/api/cities")
def list_cities() -> list[dict]:
    return [
        {
            "id": city["id"],
            "name": city["name"],
            "country": city["country"],
            "base_aqi": None,
        }
        for city in CITIES.values()
    ]


@app.get("/api/forecast")
def get_forecast(
    city_id: str = Query("delhi", description="City identifier"),
    horizon: int = Query(
        72,
        ge=24,
        le=72,
        description="Forecast horizon in hours (24-72)",
    ),
) -> dict:
    if city_id not in CITIES:
        raise HTTPException(
            status_code=404,
            detail=f"City '{city_id}' not found",
        )

    try:
        data = fetch_city_data(city_id, horizon)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unable to retrieve AQI data from Open-Meteo: {exc}",
        ) from exc

    current = data["current"]
    forecast = data["forecast"]
    history = data["recent_history"]

    peak_aqi = max(point["predicted_aqi"] for point in forecast)
    average_aqi = sum(
        point["predicted_aqi"] for point in forecast
    ) / len(forecast)

    # The API does not provide statistical confidence intervals.
    # Therefore, health guidance uses the forecast peak directly.
    guidance = generate_health_guidance(
        peak_aqi=peak_aqi,
        upper_95_peak=peak_aqi,
        avg_aqi=average_aqi,
    )

    # Replace the old confidence-interval message with an honest source note.
    guidance["uncertainty_note"] = (
        "These forecasts are atmospheric model estimates from Open-Meteo, "
        "not direct ground-station measurements. Actual local air quality "
        "may differ. No statistical confidence interval is provided."
    )

    for point in forecast:
        point["category"] = get_aqi_category(point["predicted_aqi"])

    for point in history:
        point["category"] = get_aqi_category(point["aqi"])

    return {
        "city": data["city"],
        "current": {
            **current,
            "category": get_aqi_category(current["aqi"]),
        },
        "horizon_hours": horizon,
        "best_model_id": "open_meteo",
        "model_comparisons": [],
        "feature_drivers": [],
        "recent_history": history,
        "forecast": forecast,
        "health_guidance": guidance,
        "source": data["source"],
        "source_type": data["source_type"],
        "timezone": data["timezone"],
        "updated_at": data["updated_at"],
        "is_demo_fallback": False,
    }
