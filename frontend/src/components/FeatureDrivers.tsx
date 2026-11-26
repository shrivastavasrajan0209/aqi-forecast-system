import React from "react";
import { Cpu } from "lucide-react";
import { FeatureDriver } from "../types";

interface Props {
  drivers: FeatureDriver[];
}

const GROUP_COLORS: Record<string, string> = {
  "Pollution History": "#38bdf8",
  Weather: "#10b981",
  "Traffic Indicators": "#f97316",
  "Seasonal & Cyclical": "#a855f7",
};

export const FeatureDrivers: React.FC<Props> = ({ drivers }) => {
  const maxImp = Math.max(...drivers.map((d) => d.importance), 1);

  return (
    <div className="glass-card">
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
        <Cpu size={20} color="var(--accent)" />
        <div>
          <h2 style={{ fontSize: 17, fontWeight: 600 }}>Interpretable Forecast Drivers</h2>
          <p style={{ fontSize: 12.5, color: "var(--text-muted)" }}>
            Relative feature importance across weather, traffic, seasonal trends, and pollution history.
          </p>
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {drivers.slice(0, 8).map((d) => {
          const color = GROUP_COLORS[d.group] || "#38bdf8";
          return (
            <div key={d.feature}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, marginBottom: 4 }}>
                <span>
                  {d.label}{" "}
                  <span style={{ fontSize: 11, color, marginLeft: 6, opacity: 0.9 }}>
                    {d.group}
                  </span>
                </span>
                <span className="mono" style={{ color: "var(--text-muted)" }}>
                  {d.importance.toFixed(1)}%
                </span>
              </div>
              <div style={{ width: "100%", height: 7, background: "rgba(148,163,184,0.14)", borderRadius: 999 }}>
                <div
                  style={{
                    width: `${(d.importance / maxImp) * 100}%`,
                    height: "100%",
                    borderRadius: 999,
                    background: color,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
