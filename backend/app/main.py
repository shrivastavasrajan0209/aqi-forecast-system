"""FastAPI application for the AQI Forecast & Health Guidance System."""

from __future__ import annotations

from functools import lru_cache
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .data_generator import CITIES, generate_city_history
from .health_advisor import generate_health_guidance, get_aqi_category
from .models import forecast_next_hours, train_and_compare_models

app = FastAPI(
    title="AQI Forecast & Health Guidance API",
    description="24-72h city AQI forecasting with uncertainty intervals, model comparison, and rule-based health guidance.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@lru_cache(maxsize=8)
def _get_trained_city(city_id: str) -> dict:
    raw_df = generate_city_history(city_id, hours=24 * 60)
    return train_and_compare_models(raw_df)


@app.get("/api/health")
def health_check() -> dict:
    return {"status": "ok"}


@app.get("/api/cities")
def list_cities() -> list[dict]:
    return [
        {
            "id": c.id,
            "name": c.name,
            "country": c.country,
            "base_aqi": c.base_aqi,
        }
        for c in CITIES.values()
    ]


@app.get("/api/forecast")
def get_forecast(
    city_id: str = Query("delhi", description="City identifier"),
    horizon: int = Query(72, ge=24, le=72, description="Forecast horizon in hours (24-72)"),
) -> dict:
    if city_id not in CITIES:
        raise HTTPException(status_code=404, detail=f"City '{city_id}' not found")

    trained = _get_trained_city(city_id)
    raw_df = trained["last_df"]
    recent_history = [
        {
            "timestamp": row["timestamp"].isoformat(),
            "aqi": float(row["aqi"]),
            "pm25": float(row["pm25"]),
            "temperature": float(row["temperature"]),
            "humidity": float(row["humidity"]),
            "wind_speed": float(row["wind_speed"]),
            "traffic_index": float(row["traffic_index"]),
        }
        for _, row in raw_df.iloc[-24:].iterrows()
    ]

    forecast_points = forecast_next_hours(trained, horizon_hours=horizon)
    peak_aqi = max(p["predicted_aqi"] for p in forecast_points)
    upper_95_peak = max(p["upper_95"] for p in forecast_points)
    avg_aqi = sum(p["predicted_aqi"] for p in forecast_points) / len(forecast_points)
    current_aqi = float(raw_df.iloc[-1]["aqi"])

    return {
        "city": {
            "id": CITIES[city_id].id,
            "name": CITIES[city_id].name,
            "country": CITIES[city_id].country,
        },
        "current": {
            "aqi": current_aqi,
            "category": get_aqi_category(current_aqi),
            "temperature": float(raw_df.iloc[-1]["temperature"]),
            "humidity": float(raw_df.iloc[-1]["humidity"]),
            "wind_speed": float(raw_df.iloc[-1]["wind_speed"]),
            "traffic_index": float(raw_df.iloc[-1]["traffic_index"]),
        },
        "horizon_hours": horizon,
        "best_model_id": trained["best_model_id"],
        "model_comparisons": trained["comparisons"],
        "feature_drivers": trained["feature_drivers"][:10],
        "recent_history": recent_history,
        "forecast": forecast_points,
        "health_guidance": generate_health_guidance(peak_aqi, upper_95_peak, avg_aqi),
    }
