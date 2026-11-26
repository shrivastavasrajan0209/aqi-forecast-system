
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


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
    res = client.get("/api/forecast?city_id=delhi&horizon=48")

    assert res.status_code == 200

    data = res.json()

    assert data["horizon_hours"] == 48
    assert len(data["forecast"]) == 48
    assert len(data["recent_history"]) > 0

    # Verify the data source is accurately identified.
    assert data["source"] == "Open-Meteo Air Quality API"
    assert data["source_type"] == "Atmospheric model estimates, not ground-station measurements"

    # No fabricated model comparisons or feature importance.
    assert data["model_comparisons"] == []
    assert data["feature_drivers"] == []

    # Verify forecast AQI values are valid.
    for point in data["forecast"]:
        assert point["predicted_aqi"] >= 0
        assert point["timestamp"]

    # Verify health guidance exists.
    assert len(data["health_guidance"]["groups"]) == 4


def test_invalid_horizon():
    res = client.get("/api/forecast?city_id=delhi&horizon=100")

    assert res.status_code == 422


