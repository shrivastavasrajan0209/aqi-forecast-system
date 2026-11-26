import React, { useState } from "react";
import { ForecastPoint, HistoryPoint } from "../types";

interface Props {
  history: HistoryPoint[];
  forecast: ForecastPoint[];
  horizon: number;
}

export const ForecastChart: React.FC<Props> = ({ history, forecast, horizon }) => {
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);

  const width = 920;
  const height = 320;
  const pad = { top: 20, right: 24, bottom: 38, left: 46 };
  const plotW = width - pad.left - pad.right;
  const plotH = height - pad.top - pad.bottom;

  const allValues = [
    ...history.map((h) => h.aqi),
    ...forecast.flatMap((f) => [f.lower_95, f.upper_95]),
  ];
  const maxVal = Math.max(120, Math.ceil(Math.max(...allValues) / 25) * 25);
  const minVal = 0;

  const totalPoints = history.length + forecast.length;
  const xScale = (i: number) => pad.left + (i / Math.max(1, totalPoints - 1)) * plotW;
  const yScale = (v: number) => pad.top + plotH - ((v - minVal) / (maxVal - minVal)) * plotH;

  const historyPath = history
    .map((h, i) => `${i === 0 ? "M" : "L"} ${xScale(i).toFixed(1)} ${yScale(h.aqi).toFixed(1)}`)
    .join(" ");

  const forecastStartIdx = history.length;
  const forecastPath = forecast
    .map((f, idx) => {
      const i = forecastStartIdx + idx;
      return `${idx === 0 ? "M" : "L"} ${xScale(i).toFixed(1)} ${yScale(f.predicted_aqi).toFixed(1)}`;
    })
    .join(" ");

  // Connect last history point to first forecast point
  const bridgePath =
    history.length > 0 && forecast.length > 0
      ? `M ${xScale(history.length - 1).toFixed(1)} ${yScale(history[history.length - 1].aqi).toFixed(1)} L ${xScale(
          forecastStartIdx
        ).toFixed(1)} ${yScale(forecast[0].predicted_aqi).toFixed(1)}`
      : "";

  const buildBandPath = (upperKey: "upper_95" | "upper_80", lowerKey: "lower_95" | "lower_80") => {
    if (forecast.length === 0) return "";
    const top = forecast
      .map((f, idx) => `${idx === 0 ? "M" : "L"} ${xScale(forecastStartIdx + idx).toFixed(1)} ${yScale(f[upperKey]).toFixed(1)}`)
      .join(" ");
    const bottom = [...forecast]
      .reverse()
      .map((f, rIdx) => {
        const idx = forecast.length - 1 - rIdx;
        return `L ${xScale(forecastStartIdx + idx).toFixed(1)} ${yScale(f[lowerKey]).toFixed(1)}`;
      })
      .join(" ");
    return `${top} ${bottom} Z`;
  };

  const yTicks = [0, 50, 100, 150, 200, 300].filter((t) => t <= maxVal);
  const activePoint = hoverIdx !== null && hoverIdx >= forecastStartIdx ? forecast[hoverIdx - forecastStartIdx] : null;

  return (
    <div className="glass-card" style={{ marginBottom: 20 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12, marginBottom: 14 }}>
        <div>
          <h2 style={{ fontSize: 18, fontWeight: 600 }}>
            24h History &amp; {horizon}h Probabilistic AQI Forecast
          </h2>
          <p style={{ fontSize: 13, color: "var(--text-muted)" }}>
            Shaded ribbons show 80% and 95% prediction intervals—uncertainty widens with horizon.
          </p>
        </div>
        <div style={{ display: "flex", gap: 16, fontSize: 12, color: "var(--text-muted)" }}>
          <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            <span style={{ width: 12, height: 3, background: "#94a3b8", display: "inline-block" }} /> Observed
          </span>
          <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            <span style={{ width: 12, height: 3, background: "#38bdf8", display: "inline-block" }} /> Forecast
          </span>
          <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            <span style={{ width: 12, height: 10, background: "rgba(56,189,248,0.28)", borderRadius: 2, display: "inline-block" }} /> 80% CI
          </span>
          <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            <span style={{ width: 12, height: 10, background: "rgba(56,189,248,0.12)", borderRadius: 2, display: "inline-block" }} /> 95% CI
          </span>
        </div>
      </div>

      <div style={{ position: "relative", width: "100%", overflowX: "auto" }}>
        <svg viewBox={`0 0 ${width} ${height}`} style={{ width: "100%", minWidth: 620, height: "auto", display: "block" }}>
          {yTicks.map((t) => (
            <g key={t}>
              <line x1={pad.left} x2={width - pad.right} y1={yScale(t)} y2={yScale(t)} stroke="rgba(148,163,184,0.12)" strokeDasharray="4 4" />
              <text x={pad.left - 8} y={yScale(t) + 4} textAnchor="end" fill="#94a3b8" fontSize="11" className="mono">
                {t}
              </text>
            </g>
          ))}

          {/* Now divider */}
          <line
            x1={xScale(forecastStartIdx - 0.5)}
            x2={xScale(forecastStartIdx - 0.5)}
            y1={pad.top}
            y2={height - pad.bottom}
            stroke="rgba(248, 250, 252, 0.28)"
            strokeDasharray="3 3"
          />
          <text x={xScale(forecastStartIdx - 0.5)} y={pad.top + 12} textAnchor="middle" fill="#cbd5e1" fontSize="10" className="mono">
            NOW
          </text>

          {/* Uncertainty bands */}
          <path d={buildBandPath("upper_95", "lower_95")} fill="rgba(56, 189, 248, 0.12)" />
          <path d={buildBandPath("upper_80", "lower_80")} fill="rgba(56, 189, 248, 0.25)" />

          {/* Lines */}
          <path d={historyPath} fill="none" stroke="#94a3b8" strokeWidth="2.2" />
          <path d={bridgePath} fill="none" stroke="#38bdf8" strokeWidth="2.2" strokeDasharray="4 3" />
          <path d={forecastPath} fill="none" stroke="#38bdf8" strokeWidth="2.5" />

          {/* Hover targets */}
          {forecast.map((f, idx) => {
            const i = forecastStartIdx + idx;
            return (
              <rect
                key={f.horizon_hour}
                x={xScale(i) - plotW / totalPoints / 2}
                y={pad.top}
                width={plotW / totalPoints}
                height={plotH}
                fill="transparent"
                onMouseEnter={() => setHoverIdx(i)}
                onMouseLeave={() => setHoverIdx(null)}
              />
            );
          })}

          {activePoint && hoverIdx !== null && (
            <g>
              <line
                x1={xScale(hoverIdx)}
                x2={xScale(hoverIdx)}
                y1={pad.top}
                y2={height - pad.bottom}
                stroke="rgba(56,189,248,0.6)"
                strokeWidth="1"
              />
              <circle cx={xScale(hoverIdx)} cy={yScale(activePoint.predicted_aqi)} r="4.5" fill="#38bdf8" stroke="#0f172a" strokeWidth="2" />
            </g>
          )}

          {/* X-axis labels */}
          <text x={xScale(0)} y={height - 10} textAnchor="start" fill="#94a3b8" fontSize="11" className="mono">
            -24h
          </text>
          <text x={xScale(forecastStartIdx)} y={height - 10} textAnchor="middle" fill="#94a3b8" fontSize="11" className="mono">
            +1h
          </text>
          <text x={xScale(totalPoints - 1)} y={height - 10} textAnchor="end" fill="#94a3b8" fontSize="11" className="mono">
            +{horizon}h
          </text>
        </svg>

        {activePoint && (
          <div
            style={{
              marginTop: 8,
              padding: "10px 14px",
              borderRadius: 10,
              background: "var(--surface-elevated)",
              border: "1px solid var(--border)",
              display: "flex",
              flexWrap: "wrap",
              gap: 18,
              fontSize: 13,
            }}
          >
            <span className="mono" style={{ color: "var(--accent)", fontWeight: 600 }}>
              +{activePoint.horizon_hour}h ({new Date(activePoint.timestamp).toLocaleString([], { weekday: "short", hour: "2-digit", minute: "2-digit" })})
            </span>
            <span>
              Expected AQI: <strong className="mono">{activePoint.predicted_aqi}</strong>
            </span>
            <span style={{ color: "var(--text-muted)" }}>
              80% CI: <strong className="mono">{activePoint.lower_80}–{activePoint.upper_80}</strong>
            </span>
            <span style={{ color: "var(--text-muted)" }}>
              95% CI: <strong className="mono">{activePoint.lower_95}–{activePoint.upper_95}</strong>
            </span>
            <span style={{ color: "var(--text-muted)" }}>
              Wind: <strong className="mono">{activePoint.wind_speed} km/h</strong>
            </span>
            <span style={{ color: "var(--text-muted)" }}>
              Traffic: <strong className="mono">{Math.round(activePoint.traffic_index * 100)}%</strong>
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
