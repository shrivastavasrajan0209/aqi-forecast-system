
import React from "react";
import { Activity, Wind, Info } from "lucide-react";

interface Props {
  drivers: unknown[];
}

export const FeatureDrivers: React.FC<Props> = ({ drivers }) => {
  const pollutants = [
    { name: "PM2.5", description: "Fine particulate matter" },
    { name: "PM10", description: "Coarse particulate matter" },
    { name: "NO₂", description: "Nitrogen dioxide" },
    { name: "O₃", description: "Ground-level ozone" },
    { name: "CO", description: "Carbon monoxide" },
    { name: "SO₂", description: "Sulphur dioxide" },
  ];

  return (
    <div className="glass-card">
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          marginBottom: 14,
        }}
      >
        <Activity size={20} color="var(--accent)" />

        <div>
          <h2 style={{ fontSize: 17, fontWeight: 600 }}>
            Forecast Model Information
          </h2>

          <p style={{ fontSize: 12.5, color: "var(--text-muted)" }}>
            Understanding the data behind AeroPulse.
          </p>
        </div>
      </div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          padding: 14,
          borderRadius: 10,
          background: "rgba(56,189,248,0.07)",
          border: "1px solid rgba(56,189,248,0.16)",
        }}
      >
        <Wind size={21} color="#38bdf8" />

        <div>
          <strong style={{ fontSize: 14 }}>
            Atmospheric AQI Forecast
          </strong>

          <p
            style={{
              fontSize: 12,
              color: "var(--text-muted)",
              marginTop: 4,
            }}
          >
            Forecast values are obtained from Open-Meteo atmospheric
            model estimates.
          </p>
        </div>
      </div>

      <div
        style={{
          marginTop: 16,
          display: "flex",
          alignItems: "flex-start",
          gap: 9,
          color: "var(--text-muted)",
          fontSize: 12,
          lineHeight: 1.6,
        }}
      >
        <Info size={16} style={{ flexShrink: 0, marginTop: 1 }} />

        <span>
          Feature-importance analysis is not currently available because
          the active forecasting pipeline uses Open-Meteo forecasts
          rather than a locally trained prediction model.
        </span>
      </div>
    </div>
  );
};
