from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_cities():
    res = client.get("/api/cities")
    assert res.status_code == 200
    cities = res.json()
    assert len(cities) >= 5
    assert any(c["id"] == "delhi" for c in cities)


def test_forecast_and_uncertainty():
    res = client.get("/api/forecast?city_id=delhi&horizon=48")
    assert res.status_code == 200
    data = res.json()
    assert data["horizon_hours"] == 48
    assert len(data["forecast"]) == 48
    assert len(data["model_comparisons"]) == 5
    assert any(m["model_id"] == "persistence" for m in data["model_comparisons"])
    assert len(data["feature_drivers"]) > 0
    assert len(data["health_guidance"]["groups"]) == 4

    # Verify uncertainty intervals are properly ordered
    for pt in data["forecast"]:
        assert pt["lower_95"] <= pt["lower_80"] <= pt["predicted_aqi"] <= pt["upper_80"] <= pt["upper_95"]
