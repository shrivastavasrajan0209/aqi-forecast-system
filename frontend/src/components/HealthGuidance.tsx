import React from "react";
import { AlertTriangle, HeartPulse, ShieldAlert } from "lucide-react";
import { HealthGuidance as HealthGuidanceType } from "../types";

interface Props {
  guidance: HealthGuidanceType;
}

export const HealthGuidance: React.FC<Props> = ({ guidance }) => {
  return (
    <div className="glass-card" style={{ marginBottom: 20 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 12, marginBottom: 14 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <HeartPulse size={20} color="var(--accent)" />
          <div>
            <h2 style={{ fontSize: 18, fontWeight: 600 }}>Rule-Based Health Guidance for Sensitive Groups</h2>
            <p style={{ fontSize: 13, color: "var(--text-muted)" }}>
              Actionable precautions calibrated to forecasted peak and upper-bound uncertainty.
            </p>
          </div>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <span
            style={{
              padding: "4px 10px",
              borderRadius: 999,
              fontSize: 12,
              fontWeight: 600,
              background: `${guidance.peak_category.color}22`,
              color: guidance.peak_category.color,
              border: `1px solid ${guidance.peak_category.color}55`,
            }}
          >
            Expected Peak: {guidance.peak_category.label}
          </span>
        </div>
      </div>

      <div
        style={{
          display: "flex",
          gap: 10,
          alignItems: "flex-start",
          padding: "12px 14px",
          borderRadius: 12,
          background: "rgba(245, 158, 11, 0.08)",
          border: "1px solid rgba(245, 158, 11, 0.28)",
          marginBottom: 16,
          fontSize: 13,
          color: "#fde68a",
        }}
      >
        <AlertTriangle size={18} style={{ flexShrink: 0, marginTop: 2 }} />
        <span>{guidance.uncertainty_note}</span>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 14 }}>
        {guidance.groups.map((g) => (
          <div
            key={g.group}
            style={{
              padding: 14,
              borderRadius: 12,
              background: "var(--surface-elevated)",
              border: "1px solid var(--border)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
              <span style={{ fontWeight: 600, fontSize: 14 }}>{g.group}</span>
              <span
                className="mono"
                style={{
                  fontSize: 11,
                  padding: "2px 8px",
                  borderRadius: 999,
                  background: "rgba(56, 189, 248, 0.14)",
                  color: "var(--accent)",
                }}
              >
                <ShieldAlert size={11} style={{ display: "inline", marginRight: 4, verticalAlign: "-1px" }} />
                {g.risk}
              </span>
            </div>
            <p style={{ fontSize: 13, color: "var(--text-muted)" }}>{g.advice}</p>
          </div>
        ))}
      </div>
    </div>
  );
};
