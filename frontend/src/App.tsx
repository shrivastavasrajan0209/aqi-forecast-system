
import React, { useEffect, useState } from "react";
import {
  Activity,
  Car,
  Droplets,
  MapPin,
  Thermometer,
  Wind,
} from "lucide-react";

import { fetchCities, fetchForecast } from "./api";
import { CityInfo, ForecastResponse } from "./types";
import { ForecastChart } from "./components/ForecastChart";
import { HealthGuidance } from "./components/HealthGuidance";
import { ModelComparison } from "./components/ModelComparison";
import { FeatureDrivers } from "./components/FeatureDrivers";

export default function App() {
  const [cities, setCities] = useState<CityInfo[]>([]);
  const [selectedCity, setSelectedCity] = useState<string>("delhi");
  const [horizon, setHorizon] = useState<number>(72);
  const [data, setData] = useState<ForecastResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCities().then(setCities).catch(console.error);
  }, []);

  useEffect(() => {
    let cancelled = false;

    setLoading(true);
    setError(null);

    fetchForecast(selectedCity, horizon)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load AQI forecast."
          );
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [selectedCity, horizon]);

  const hasTraffic =
    data?.current.traffic_index != null &&
    Number.isFinite(data.current.traffic_index);

  return (
    <div className="app-shell">
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 16,
          marginBottom: 24,
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div
              style={{
                width: 36,
                height: 36,
                borderRadius: 10,
                background: "linear-gradient(135deg, #38bdf8, #10b981)",
                display: "grid",
                placeItems: "center",
                color: "#070b14",
                fontWeight: 800,
              }}
            >
              <Activity size={20} />
            </div>

            <h1
              style={{
                fontSize: 24,
                fontWeight: 700,
                letterSpacing: "-0.02em",
              }}
            >
              AeroPulse{" "}
              <span style={{ color: "var(--accent)", fontWeight: 500 }}>
                AQI Forecast
              </span>
            </h1>
          </div>

          <p
            style={{
              fontSize: 13.5,
              color: "var(--text-muted)",
              marginTop: 4,
            }}
          >
            24–72h AQI forecasts using Open-Meteo atmospheric model
            estimates and rule-based health guidance.
          </p>
        </div>

        <div
          style={{
            display: "flex",
            gap: 10,
            alignItems: "center",
            flexWrap: "wrap",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: 12,
              padding: "6px 12px",
            }}
          >
            <MapPin size={16} color="var(--accent)" />

            <select
              value={selectedCity}
              onChange={(e) => setSelectedCity(e.target.value)}
              style={{
                background: "transparent",
                color: "var(--text)",
                border: "none",
                outline: "none",
                fontSize: 14,
                fontWeight: 500,
                cursor: "pointer",
              }}
            >
              {cities.map((city) => (
                <option
                  key={city.id}
                  value={city.id}
                  style={{ background: "#0f172a" }}
                >
                  {city.name}, {city.country}
                </option>
              ))}
            </select>
          </div>

          <div
            style={{
              display: "flex",
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: 12,
              padding: 4,
            }}
          >
            {[24, 48, 72].map((hours) => (
              <button
                key={hours}
                onClick={() => setHorizon(hours)}
                className="mono"
                style={{
                  padding: "6px 12px",
                  borderRadius: 8,
                  border: "none",
                  cursor: "pointer",
                  fontSize: 13,
                  fontWeight: 600,
                  background:
                    horizon === hours
                      ? "var(--accent)"
                      : "transparent",
                  color:
                    horizon === hours
                      ? "#070b14"
                      : "var(--text-muted)",
                }}
              >
                {hours}h
              </button>
            ))}
          </div>
        </div>
      </header>

      {data?.is_demo_fallback && (
        <div
          style={{
            marginBottom: 16,
            padding: "10px 14px",
            borderRadius: 12,
            background: "rgba(245,158,11,0.1)",
            border: "1px solid rgba(245,158,11,0.25)",
            fontSize: 13,
            color: "#fcd34d",
          }}
        >
          Demo preview: the backend could not provide current API data.
          Displayed values are simulated and are not live measurements.
        </div>
      )}

      {loading && !data ? (
        <div
          className="glass-card"
          style={{
            textAlign: "center",
            padding: 48,
            color: "var(--text-muted)",
          }}
        >
          <Activity
            size={24}
            style={{ marginBottom: 12 }}
            color="var(--accent)"
          />
          <p>Loading air quality data and forecasts...</p>
        </div>
      ) : error && !data ? (
        <div
          className="glass-card"
          style={{
            textAlign: "center",
            padding: 40,
            color: "var(--text-muted)",
          }}
        >
          <p style={{ color: "#f87171", marginBottom: 10 }}>
            Unable to load forecast
          </p>
          <p>{error}</p>

          <button
            onClick={() => {
              setSelectedCity((current) => current);
              setHorizon((current) => current);
            }}
            style={{ marginTop: 16 }}
          >
            Try again
          </button>
        </div>
      ) : (
        data && (
          <>
            {loading && (
              <p
                style={{
                  color: "var(--text-muted)",
                  fontSize: 12,
                  marginBottom: 12,
                }}
              >
                Updating forecast...
              </p>
            )}

            {/* AQI and weather indicators */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns:
                  "repeat(auto-fit, minmax(190px, 1fr))",
                gap: 14,
                marginBottom: 20,
              }}
            >
              <div
                className="glass-card"
                style={{
                  borderColor: `${data.current.category.color}55`,
                }}
              >
                <div
                  style={{
                    fontSize: 12,
                    color: "var(--text-muted)",
                    marginBottom: 4,
                  }}
                >
                  Current AQI
                </div>

                <div
                  style={{
                    display: "flex",
                    alignItems: "baseline",
                    gap: 10,
                  }}
                >
                  <span
                    className="mono"
                    style={{
                      fontSize: 30,
                      fontWeight: 700,
                      color: data.current.category.color,
                    }}
                  >
                    {Math.round(data.current.aqi)}
                  </span>

                  <span
                    style={{
                      fontSize: 12.5,
                      fontWeight: 600,
                      color: data.current.category.color,
                    }}
                  >
                    {data.current.category.label}
                  </span>
                </div>
              </div>

              <div className="glass-card">
                <div
                  style={{
                    fontSize: 12,
                    color: "var(--text-muted)",
                    marginBottom: 4,
                  }}
                >
                  Temperature
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <Thermometer size={18} color="#f59e0b" />

                  <span className="mono" style={{ fontSize: 22, fontWeight: 600 }}>
                    {data.current.temperature}°C
                  </span>
                </div>
              </div>

              <div className="glass-card">
                <div
                  style={{
                    fontSize: 12,
                    color: "var(--text-muted)",
                    marginBottom: 4,
                  }}
                >
                  Wind Speed
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <Wind size={18} color="#38bdf8" />

                  <span className="mono" style={{ fontSize: 22, fontWeight: 600 }}>
                    {data.current.wind_speed} km/h
                  </span>
                </div>
              </div>

              <div className="glass-card">
                <div
                  style={{
                    fontSize: 12,
                    color: "var(--text-muted)",
                    marginBottom: 4,
                  }}
                >
                  Humidity
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <Droplets size={18} color="#10b981" />

                  <span className="mono" style={{ fontSize: 22, fontWeight: 600 }}>
                    {data.current.humidity}%
                  </span>
                </div>
              </div>

              {hasTraffic && (
                <div className="glass-card">
                  <div
                    style={{
                      fontSize: 12,
                      color: "var(--text-muted)",
                      marginBottom: 4,
                    }}
                  >
                    Traffic Index
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <Car size={18} color="#f97316" />

                    <span className="mono" style={{ fontSize: 22, fontWeight: 600 }}>
                      {Math.round(data.current.traffic_index! * 100)}%
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Forecast graph */}
            <ForecastChart
              history={data.recent_history}
              forecast={data.forecast}
              horizon={data.horizon_hours}
            />

            {/* Health guidance */}
            <HealthGuidance guidance={data.health_guidance} />

            {/* Data source and feature information */}
            <div className="grid-2">
              <ModelComparison />
              <FeatureDrivers drivers={data.feature_drivers} />
            </div>
          </>
        )
      )}
    </div>
  );
}
