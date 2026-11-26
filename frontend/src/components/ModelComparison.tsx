import React from "react";
import { BarChart3, Trophy } from "lucide-react";
import { ModelComparison as ModelComparisonType } from "../types";

interface Props {
  models: ModelComparisonType[];
  bestModelId: string;
}

export const ModelComparison: React.FC<Props> = ({ models, bestModelId }) => {
  const maxRmse = Math.max(...models.map((m) => m.rmse), 1);

  return (
    <div className="glass-card">
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
        <BarChart3 size={20} color="var(--accent)" />
        <div>
          <h2 style={{ fontSize: 17, fontWeight: 600 }}>Model Benchmark vs. Persistence Baseline</h2>
          <p style={{ fontSize: 12.5, color: "var(--text-muted)" }}>
            Out-of-sample evaluation comparing Regression, Tree Ensembles, and SARIMAX Time-Series.
          </p>
        </div>
      </div>

      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: "1px solid var(--border)", color: "var(--text-muted)", textAlign: "left" }}>
              <th style={{ padding: "8px 6px" }}>Model</th>
              <th style={{ padding: "8px 6px" }}>Family</th>
              <th style={{ padding: "8px 6px" }}>MAE</th>
              <th style={{ padding: "8px 6px" }}>RMSE</th>
              <th style={{ padding: "8px 6px" }}>R²</th>
              <th style={{ padding: "8px 6px" }}>Skill vs. Persist</th>
            </tr>
          </thead>
          <tbody>
            {models.map((m) => {
              const isBest = m.model_id === bestModelId;
              return (
                <tr
                  key={m.model_id}
                  style={{
                    borderBottom: "1px solid rgba(148,163,184,0.08)",
                    background: isBest ? "rgba(56, 189, 248, 0.08)" : "transparent",
                  }}
                >
                  <td style={{ padding: "10px 6px", fontWeight: isBest ? 600 : 500 }}>
                    {m.name}
                    {isBest && (
                      <span
                        style={{
                          marginLeft: 6,
                          fontSize: 11,
                          color: "#38bdf8",
                          display: "inline-flex",
                          alignItems: "center",
                          gap: 3,
                        }}
                      >
                        <Trophy size={12} /> Active
                      </span>
                    )}
                  </td>
                  <td style={{ padding: "10px 6px", color: "var(--text-muted)" }}>{m.family}</td>
                  <td className="mono" style={{ padding: "10px 6px" }}>{m.mae.toFixed(2)}</td>
                  <td className="mono" style={{ padding: "10px 6px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span>{m.rmse.toFixed(2)}</span>
                      <div style={{ width: 52, height: 6, background: "rgba(148,163,184,0.15)", borderRadius: 999 }}>
                        <div
                          style={{
                            width: `${(m.rmse / maxRmse) * 100}%`,
                            height: "100%",
                            borderRadius: 999,
                            background: isBest ? "#38bdf8" : "#64748b",
                          }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="mono" style={{ padding: "10px 6px" }}>{m.r2.toFixed(3)}</td>
                  <td
                    className="mono"
                    style={{
                      padding: "10px 6px",
                      color: m.skill_score_vs_persistence > 0 ? "#10b981" : "var(--text-muted)",
                    }}
                  >
                    {m.skill_score_vs_persistence > 0 ? `+${(m.skill_score_vs_persistence * 100).toFixed(1)}%` : "0.0%"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
