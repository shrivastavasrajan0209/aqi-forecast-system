
import React, { useState } from "react";
import { ForecastPoint, HistoryPoint } from "../types";

interface Props {
  history: HistoryPoint[];
  forecast: ForecastPoint[];
  horizon: number;
}

export const ForecastChart: React.FC<Props> = ({
  history,
  forecast,
  horizon,
}) => {
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);

  const width = 920;
  const height = 340;

  const pad = {
    top: 25,
    right: 30,
    bottom: 45,
    left: 55,
  };

  const plotW = width - pad.left - pad.right;
  const plotH = height - pad.top - pad.bottom;

  // Remove invalid or missing AQI values.
  const validHistory = history.filter(
    (point) => Number.isFinite(point.aqi)
  );

  const validForecast = forecast.filter(
    (point) => Number.isFinite(point.predicted_aqi)
  );

  const totalPoints = validHistory.length + validForecast.length;

  if (totalPoints === 0) {
    return (
      <div className="glass-card" style={{ marginBottom: 20 }}>
        <h2 style={{ fontSize: 18 }}>AQI Forecast</h2>
        <p style={{ color: "var(--text-muted)" }}>
          No valid chart data is currently available.
        </p>
      </div>
    );
  }

  const values = [
    ...validHistory.map((point) => point.aqi),
    ...validForecast.map((point) => point.predicted_aqi),
  ];

  const rawMax = Math.max(...values);
  const maxVal = Math.max(
    100,
    Math.ceil((rawMax * 1.15) / 50) * 50
  );

  const minVal = 0;

  const xScale = (index: number) =>
    pad.left +
    (index / Math.max(1, totalPoints - 1)) * plotW;

  const yScale = (value: number) =>
    pad.top +
    plotH -
    ((value - minVal) / (maxVal - minVal)) * plotH;

  // Historical AQI line.
  const historyPath = validHistory
    .map(
      (point, index) =>
        `${index === 0 ? "M" : "L"} ${xScale(index)} ${yScale(
          point.aqi
        )}`
    )
    .join(" ");

  // Forecast AQI line.
  const forecastStartIdx = validHistory.length;

  const forecastPath = validForecast
    .map(
      (point, index) =>
        `${index === 0 ? "M" : "L"} ${xScale(
          forecastStartIdx + index
        )} ${yScale(point.predicted_aqi)}`
    )
    .join(" ");

  // Connect historical data to forecast.
  const bridgePath =
    validHistory.length > 0 && validForecast.length > 0
      ? `M ${xScale(validHistory.length - 1)} ${yScale(
          validHistory[validHistory.length - 1].aqi
        )} L ${xScale(forecastStartIdx)} ${yScale(
          validForecast[0].predicted_aqi
        )}`
      : "";

  const tickStep = maxVal <= 200 ? 25 : 50;

  const yTicks = Array.from(
    { length: Math.floor(maxVal / tickStep) + 1 },
    (_, index) => index * tickStep
  );

  const activePoint =
    hoverIdx !== null && hoverIdx >= forecastStartIdx
      ? validForecast[hoverIdx - forecastStartIdx]
      : null;

  return (
    <div className="glass-card" style={{ marginBottom: 20 }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 12,
          marginBottom: 18,
        }}
      >
        <div>
          <h2 style={{ fontSize: 18, fontWeight: 600 }}>
            24h History &amp; {horizon}h AQI Forecast
          </h2>

          <p
            style={{
              fontSize: 13,
              color: "var(--text-muted)",
              marginTop: 5,
            }}
          >
            Historical and forecast values from Open-Meteo atmospheric
            model estimates.
          </p>
        </div>

        <div
          style={{
            display: "flex",
            gap: 16,
            fontSize: 12,
            color: "var(--text-muted)",
            flexWrap: "wrap",
          }}
        >
          <span>
            <span style={{ color: "#94a3b8" }}>━</span> Historical estimates
          </span>

          <span>
            <span style={{ color: "#38bdf8" }}>━</span> Forecast
          </span>
        </div>
      </div>

      <div style={{ width: "100%", overflowX: "auto" }}>
        <svg
          viewBox={`0 0 ${width} ${height}`}
          style={{
            width: "100%",
            minWidth: 620,
            height: "auto",
            display: "block",
          }}
        >
          {/* Horizontal grid and Y-axis labels */}
          {yTicks.map((tick) => (
            <g key={tick}>
              <line
                x1={pad.left}
                x2={width - pad.right}
                y1={yScale(tick)}
                y2={yScale(tick)}
                stroke="rgba(148,163,184,0.15)"
                strokeDasharray="4 4"
              />

              <text
                x={pad.left - 10}
                y={yScale(tick) + 4}
                textAnchor="end"
                fill="#94a3b8"
                fontSize="11"
              >
                {tick}
              </text>
            </g>
          ))}

          {/* Current time divider */}
          {validHistory.length > 0 && validForecast.length > 0 && (
            <>
              <line
                x1={xScale(forecastStartIdx - 0.5)}
                x2={xScale(forecastStartIdx - 0.5)}
                y1={pad.top}
                y2={height - pad.bottom}
                stroke="rgba(248,250,252,0.4)"
                strokeDasharray="4 4"
              />

              <text
                x={xScale(forecastStartIdx - 0.5)}
                y={pad.top + 12}
                textAnchor="middle"
                fill="#cbd5e1"
                fontSize="10"
              >
                NOW
              </text>
            </>
          )}

          {/* Historical line */}
          <path
            d={historyPath}
            fill="none"
            stroke="#94a3b8"
            strokeWidth="2.5"
            strokeLinejoin="round"
            strokeLinecap="round"
          />

          {/* Connect history and forecast */}
          <path
            d={bridgePath}
            fill="none"
            stroke="#38bdf8"
            strokeWidth="2"
            strokeDasharray="5 5"
          />

          {/* Forecast line */}
          <path
            d={forecastPath}
            fill="none"
            stroke="#38bdf8"
            strokeWidth="2.8"
            strokeLinejoin="round"
            strokeLinecap="round"
          />

          {/* Forecast points */}
          {validForecast.map((point, index) => {
            const chartIndex = forecastStartIdx + index;

            return (
              <g key={`${point.horizon_hour}-${index}`}>
                <circle
                  cx={xScale(chartIndex)}
                  cy={yScale(point.predicted_aqi)}
                  r={hoverIdx === chartIndex ? 6 : 3}
                  fill="#38bdf8"
                  stroke="#0f172a"
                  strokeWidth="2"
                />

                <rect
                  x={xScale(chartIndex) - plotW / totalPoints / 2}
                  y={pad.top}
                  width={Math.max(1, plotW / totalPoints)}
                  height={plotH}
                  fill="transparent"
                  onMouseEnter={() => setHoverIdx(chartIndex)}
                  onMouseLeave={() => setHoverIdx(null)}
                />
              </g>
            );
          })}

          {/* Hover indicator */}
          {activePoint && hoverIdx !== null && (
            <g>
              <line
                x1={xScale(hoverIdx)}
                x2={xScale(hoverIdx)}
                y1={pad.top}
                y2={height - pad.bottom}
                stroke="#38bdf8"
                strokeDasharray="4 4"
              />

              <circle
                cx={xScale(hoverIdx)}
                cy={yScale(activePoint.predicted_aqi)}
                r="6"
                fill="#38bdf8"
                stroke="#ffffff"
                strokeWidth="2"
              />
            </g>
          )}

          {/* X-axis labels */}
          <text
            x={xScale(0)}
            y={height - 12}
            textAnchor="start"
            fill="#94a3b8"
            fontSize="11"
          >
            -24h
          </text>

          {validForecast.length > 0 && (
            <>
              <text
                x={xScale(forecastStartIdx)}
                y={height - 12}
                textAnchor="middle"
                fill="#94a3b8"
                fontSize="11"
              >
                +1h
              </text>

              <text
                x={xScale(totalPoints - 1)}
                y={height - 12}
                textAnchor="end"
                fill="#94a3b8"
                fontSize="11"
              >
                +{horizon}h
              </text>
            </>
          )}
        </svg>

        {/* Hover details */}
        {activePoint && (
          <div
            style={{
              marginTop: 12,
              padding: "12px 16px",
              borderRadius: 10,
              background: "var(--surface-elevated)",
              border: "1px solid var(--border)",
              display: "flex",
              flexWrap: "wrap",
              gap: 18,
              fontSize: 13,
            }}
          >
            <span
              style={{
                color: "var(--accent)",
                fontWeight: 600,
              }}
            >
              +{activePoint.horizon_hour}h (
              {new Date(activePoint.timestamp).toLocaleString([], {
                weekday: "short",
                hour: "2-digit",
                minute: "2-digit",
              })}
              )
            </span>

            <span>
              Forecast AQI:{" "}
              <strong>
                {Math.round(activePoint.predicted_aqi)}
              </strong>
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
