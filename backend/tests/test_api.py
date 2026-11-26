
from datetime import datetime, timedelta
from unittest.mock import patch

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def make_mock_data(horizon):
    """Create deterministic provider data for offline API tests."""

    start = datetime(2026, 11, 26, 0, 0)

    history = [
        {
            "timestamp": (start - timedelta(hours=24 - i)).isoformat(),
            "aqi": 65,
            "pm25": 18.5,
            "pm10": 30.0,
            "temperature": 25.0,
            "humidity": 55.0,
            "wind_speed": 8.0,
            "traffic_index": None,
        }
        for i in range(24)
    ]

    forecast = [
        {
            "horizon_hour": i,
            "timestamp": (start + timedelta(hours=i)).isoformat(),
            "predicted_aqi": 70 + (i % 10),
            "pm25": 20.0,
            "pm10": 32.0,
            "temperature": 26.0,
            "humidity": 50.0,
            "wind_speed": 9.0,
            "traffic_index": None,
        }
        for i in range(1, horizon + 1)
    ]

    return {
        "city": {
            "id": "delhi",
            "name": "New Delhi",
            "country": "India",
        },
        "current": {
            "aqi": 68,
            "pm25": 19.0,
            "pm10": 31.0,
            "no2": 12.0,
            "ozone": 40.0,
            "co": 200.0,
            "so2": 5.0,
            "temperature": 25.0,
            "humidity": 55.0,
            "wind_speed": 8.0,
            "traffic_index": None,
        },
        "recent_history": history,
        "forecast": forecast,
        "source": "Open-Meteo Air Quality API",
        "source_type": (
            "Atmospheric model estimates, "
            "not ground-station measurements"
        ),
        "timezone": "Asia/Kolkata",
        "updated_at": start.isoformat(),
    }


def test_health():
    res = client.get("/api/health")

    assert res.status_code == 200

    data = res.json()
    assert data["status"] == "ok"
    assert data["data_source"] == "Open-Meteo"
    assert data["forecast_type"] == "Atmospheric model estimates"


def test_cities():
    res = client.get("/api/cities")

    assert res.status_code == 200

    cities = res.json()
    assert len(cities) >= 5
    assert any(city["id"] == "delhi" for city in cities)


def test_forecast():
    mock_data = make_mock_data(48)

    with patch("app.main.fetch_city_data", return_value=mock_data):
        res = client.get(
            "/api/forecast?city_id=delhi&horizon=48"
        )

    assert res.status_code == 200

    data = res.json()

    assert data["horizon_hours"] == 48
    assert len(data["forecast"]) == 48
    assert len(data["recent_history"]) == 24

    assert data["source"] == "Open-Meteo Air Quality API"
    assert data["source_type"] == (
        "Atmospheric model estimates, "
        "not ground-station measurements"
    )

    assert data["model_comparisons"] == []
    assert data["feature_drivers"] == []

    for point in data["forecast"]:
        assert point["predicted_aqi"] >= 0
        assert point["timestamp"]

    assert len(data["health_guidance"]["groups"]) == 4
    assert data["is_demo_fallback"] is False


def test_invalid_horizon():
    res = client.get(
        "/api/forecast?city_id=delhi&horizon=100"
    )

    assert res.status_code == 422


def test_unknown_city():
    res = client.get(
        "/api/forecast?city_id=unknown&horizon=48"
    )

    assert res.status_code == 404
