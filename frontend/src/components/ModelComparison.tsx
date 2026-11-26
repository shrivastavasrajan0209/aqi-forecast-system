
import React from "react";
import { BarChart3, Cloud, Info, Activity } from "lucide-react";

export const ModelComparison: React.FC = () => {
  return (
    <div className="glass-card">
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          marginBottom: 16,
        }}
      >
        <Cloud size={21} color="var(--accent)" />

        <div>
          <h2 style={{ fontSize: 17, fontWeight: 600 }}>
            Forecast Data Source
          </h2>

          <p style={{ fontSize: 12.5, color: "var(--text-muted)" }}>
            Atmospheric data powering AeroPulse predictions.
          </p>
        </div>
      </div>

      <div
        style={{
          padding: 16,
          borderRadius: 12,
          background: "rgba(56,189,248,0.07)",
          border: "1px solid rgba(56,189,248,0.18)",
          marginBottom: 14,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Activity size={17} color="#38bdf8" />

          <strong style={{ fontSize: 14 }}>
            Open-Meteo Air Quality API
          </strong>
        </div>

        <p
          style={{
            fontSize: 13,
            color: "var(--text-muted)",
            lineHeight: 1.7,
            marginTop: 9,
          }}
        >
          AeroPulse uses atmospheric model estimates from Open-Meteo
          to retrieve current air-quality information, recent
          historical estimates, and forecasts for the next 24–72 hours.
        </p>
      </div>

      <div style={{ display: "grid", gap: 12 }}>
        <div>
          <p style={{ fontSize: 12, color: "var(--text-muted)" }}>
            Forecast horizon
          </p>
          <strong style={{ fontSize: 14 }}>24–72 hours</strong>
        </div>

        <div>
          <p style={{ fontSize: 12, color: "var(--text-muted)" }}>
            Data type
          </p>
          <strong style={{ fontSize: 14 }}>
            Atmospheric model estimates
          </strong>
        </div>

        <div>
          <p style={{ fontSize: 12, color: "var(--text-muted)" }}>
            Forecast methodology
          </p>
          <strong style={{ fontSize: 14 }}>
            Open-Meteo forecast data
          </strong>
        </div>
      </div>

      <div
        style={{
          display: "flex",
          gap: 9,
          marginTop: 16,
          paddingTop: 13,
          borderTop: "1px solid var(--border)",
          color: "var(--text-muted)",
          fontSize: 12,
          lineHeight: 1.6,
        }}
      >
        <Info size={16} style={{ flexShrink: 0, marginTop: 1 }} />

        <span>
          These values are not direct ground-station measurements.
          Forecasts may differ from actual local air quality.
          Statistical model benchmarking is not currently enabled.
        </span>
      </div>
    </div>
  );
};
