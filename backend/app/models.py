"""Model training, comparison against persistence baseline, recursive 72h forecasting, and uncertainty estimation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.statespace.sarimax import SARIMAX

from .features import FEATURE_COLUMNS, FEATURE_GROUPS, FEATURE_LABELS, engineer_features


@dataclass
class ModelMetrics:
    model_id: str
    name: str
    family: str
    mae: float
    rmse: float
    r2: float
    skill_score_vs_persistence: float


def _evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray, persistence_rmse: float) -> tuple[float, float, float, float]:
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = float(r2_score(y_true, y_pred))
    skill = float(1.0 - (rmse / persistence_rmse)) if persistence_rmse > 0 else 0.0
    return round(mae, 2), round(rmse, 2), round(r2, 3), round(skill, 3)


def train_and_compare_models(raw_df: pd.DataFrame) -> dict:
    """Train Regression, Tree-Ensemble, and Time-Series models, compare with Persistence baseline."""
    feat_df = engineer_features(raw_df).dropna().reset_index(drop=True)

    split_idx = int(len(feat_df) * 0.8)
    train_df = feat_df.iloc[:split_idx]
    test_df = feat_df.iloc[split_idx:]

    X_train = train_df[FEATURE_COLUMNS].values
    y_train = train_df["aqi"].values
    X_test = test_df[FEATURE_COLUMNS].values
    y_test = test_df["aqi"].values

    # 1. Persistence Baseline: AQI(t) = AQI(t - 1)
    y_pred_persist = test_df["aqi_lag_1"].values
    persist_rmse = float(np.sqrt(mean_squared_error(y_test, y_pred_persist)))
    p_mae, p_rmse, p_r2, p_skill = _evaluate_predictions(y_test, y_pred_persist, persist_rmse)

    # 2. Regression: Ridge Regression
    ridge = Pipeline([("scaler", StandardScaler()), ("model", Ridge(alpha=2.0))])
    ridge.fit(X_train, y_train)
    y_pred_ridge = ridge.predict(X_test)
    r_mae, r_rmse, r_r2, r_skill = _evaluate_predictions(y_test, y_pred_ridge, persist_rmse)

    # 3. Tree-Ensemble 1: Random Forest
    rf = RandomForestRegressor(n_estimators=120, max_depth=12, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    y_pred_rf = rf.predict(X_test)
    rf_mae, rf_rmse, rf_r2, rf_skill = _evaluate_predictions(y_test, y_pred_rf, persist_rmse)

    # 4. Tree-Ensemble 2: HistGradientBoosting
    hgb = HistGradientBoostingRegressor(max_iter=150, max_depth=6, learning_rate=0.06, random_state=42)
    hgb.fit(X_train, y_train)
    y_pred_hgb = hgb.predict(X_test)
    hgb_mae, hgb_rmse, hgb_r2, hgb_skill = _evaluate_predictions(y_test, y_pred_hgb, persist_rmse)

    # 5. Time-Series: SARIMAX(2, 0, 1) on recent 14 days for fast, realistic comparison
    ts_train = train_df["aqi"].values[-24 * 14 :]
    sarimax_model = SARIMAX(ts_train, order=(2, 0, 1), enforce_stationarity=False, enforce_invertibility=False)
    sarimax_fit = sarimax_model.fit(disp=False)
    # One-step-ahead in-sample/out-of-sample filtering on test_df
    sarimax_test = sarimax_fit.apply(test_df["aqi"].values)
    y_pred_ts = sarimax_test.fittedvalues
    ts_mae, ts_rmse, ts_r2, ts_skill = _evaluate_predictions(y_test, y_pred_ts, persist_rmse)

    comparisons = [
        ModelMetrics("persistence", "Persistence Baseline", "Baseline", p_mae, p_rmse, p_r2, p_skill),
        ModelMetrics("ridge", "Ridge Regression", "Regression", r_mae, r_rmse, r_r2, r_skill),
        ModelMetrics("random_forest", "Random Forest", "Tree Ensemble", rf_mae, rf_rmse, rf_r2, rf_skill),
        ModelMetrics("hist_gbm", "HistGradientBoosting", "Tree Ensemble", hgb_mae, hgb_rmse, hgb_r2, hgb_skill),
        ModelMetrics("sarimax", "SARIMAX (2,0,1)", "Time Series", ts_mae, ts_rmse, ts_r2, ts_skill),
    ]

    # Pick best ML model by RMSE (excluding persistence)
    ml_models = {"ridge": (ridge, r_rmse, y_pred_ridge), "random_forest": (rf, rf_rmse, y_pred_rf), "hist_gbm": (hgb, hgb_rmse, y_pred_hgb)}
    best_id = min(ml_models, key=lambda k: ml_models[k][1])
    best_model, _, best_test_preds = ml_models[best_id]

    # Residual std for conformal-style horizon-scaled uncertainty intervals
    residuals = y_test - best_test_preds
    residual_std = float(np.std(residuals))

    # Feature importances from Random Forest (interpretable across all features)
    importances = rf.feature_importances_
    feature_drivers = sorted(
        [
            {
                "feature": col,
                "label": FEATURE_LABELS[col],
                "group": FEATURE_GROUPS[col],
                "importance": round(float(imp) * 100, 2),
            }
            for col, imp in zip(FEATURE_COLUMNS, importances)
        ],
        key=lambda x: x["importance"],
        reverse=True,
    )

    return {
        "comparisons": [m.__dict__ for m in comparisons],
        "best_model_id": best_id,
        "best_model": best_model,
        "residual_std": residual_std,
        "feature_drivers": feature_drivers,
        "last_df": raw_df,
    }


def forecast_next_hours(trained: dict, horizon_hours: int = 72) -> list[dict]:
    """Generate 24-72h recursive forecast with 80% and 95% uncertainty intervals."""
    df = trained["last_df"].copy()
    model = trained["best_model"]
    sigma_1h = max(trained["residual_std"], 4.0)

    last_row = df.iloc[-1]
    last_ts = pd.to_datetime(last_row["timestamp"])
    forecasts: list[dict] = []

    # Simulate future weather & traffic using diurnal/synoptic patterns
    for h in range(1, horizon_hours + 1):
        next_ts = last_ts + timedelta(hours=h)
        hour = next_ts.hour
        dow = next_ts.weekday()

        # Diurnal weather continuation
        temp = float(last_row["temperature"]) + 3.5 * np.sin(2 * np.pi * (hour - 9) / 24.0) * 0.25
        humidity = float(np.clip(last_row["humidity"] - 4.0 * np.sin(2 * np.pi * (hour - 9) / 24.0) * 0.25, 20.0, 95.0))
        wind = float(np.clip(last_row["wind_speed"] + 1.5 * np.sin(2 * np.pi * (hour - 11) / 24.0) * 0.3, 1.0, 25.0))
        pressure = float(last_row["pressure"])
        precip = 0.0

        is_weekend = 1.0 if dow >= 5 else 0.0
        morning_peak = np.exp(-0.5 * ((hour - 9.0) / 1.8) ** 2)
        evening_peak = np.exp(-0.5 * ((hour - 18.5) / 2.2) ** 2)
        traffic = float(np.clip((0.25 + 0.65 * (morning_peak + 1.1 * evening_peak)) * (1.0 - 0.28 * is_weekend), 0.08, 1.0))

        new_row = {
            "timestamp": next_ts,
            "aqi": float(df.iloc[-1]["aqi"]),  # placeholder before prediction
            "pm25": float(df.iloc[-1]["pm25"]),
            "pm10": float(df.iloc[-1]["pm10"]),
            "no2": float(18.0 + 45.0 * traffic),
            "o3": float(df.iloc[-1]["o3"]),
            "temperature": round(temp, 1),
            "humidity": round(humidity, 1),
            "wind_speed": round(wind, 1),
            "pressure": round(pressure, 1),
            "precipitation": precip,
            "traffic_index": round(traffic, 3),
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        feat_df = engineer_features(df.iloc[-30:]).iloc[-1:]
        X_next = feat_df[FEATURE_COLUMNS].values
        pred_aqi = float(np.clip(model.predict(X_next)[0], 10.0, 480.0))
        df.at[df.index[-1], "aqi"] = pred_aqi
        df.at[df.index[-1], "pm25"] = pred_aqi * 0.42

        # Uncertainty grows with sqrt(horizon)
        sigma_h = sigma_1h * np.sqrt(1.0 + 0.14 * h)
        ci80_half = 1.28 * sigma_h
        ci95_half = 1.96 * sigma_h

        forecasts.append(
            {
                "horizon_hour": h,
                "timestamp": next_ts.isoformat(),
                "predicted_aqi": round(pred_aqi, 1),
                "lower_80": round(max(5.0, pred_aqi - ci80_half), 1),
                "upper_80": round(min(500.0, pred_aqi + ci80_half), 1),
                "lower_95": round(max(5.0, pred_aqi - ci95_half), 1),
                "upper_95": round(min(500.0, pred_aqi + ci95_half), 1),
                "uncertainty_std": round(sigma_h, 1),
                "traffic_index": round(traffic, 2),
                "wind_speed": round(wind, 1),
                "temperature": round(temp, 1),
                "humidity": round(humidity, 1),
            }
        )

    return forecasts
