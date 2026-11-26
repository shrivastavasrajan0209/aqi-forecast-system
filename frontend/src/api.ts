import { CityInfo, ForecastResponse } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

export const DEMO_CITIES: CityInfo[] = [
  { id: "delhi", name: "New Delhi", country: "India", base_aqi: 155 },
  { id: "los-angeles", name: "Los Angeles", country: "USA", base_aqi: 68 },
  { id: "london", name: "London", country: "UK", base_aqi: 42 },
  { id: "beijing", name: "Beijing", country: "China", base_aqi: 112 },
  { id: "bengaluru", name: "Bengaluru", country: "India", base_aqi: 76 },
];

export async function fetchCities(): Promise<CityInfo[]> {
  try {
    const res = await fetch(`${API_BASE}/api/cities`);
    if (!res.ok) throw new Error("Failed to fetch cities");
    return await res.json();
  } catch {
    return DEMO_CITIES;
  }
}

export async function fetchForecast(cityId: string, horizon: number): Promise<ForecastResponse> {
  try {
    const res = await fetch(`${API_BASE}/api/forecast?city_id=${encodeURIComponent(cityId)}&horizon=${horizon}`);
    if (!res.ok) throw new Error("API unavailable");
    return await res.json();
  } catch {
    return buildDemoForecast(cityId, horizon);
  }
}

function getCategory(aqi: number) {
  if (aqi <= 50) return { label: "Good", color: "#10b981", level: 1 };
  if (aqi <= 100) return { label: "Moderate", color: "#f59e0b", level: 2 };
  if (aqi <= 150) return { label: "Unhealthy for Sensitive Groups", color: "#f97316", level: 3 };
  if (aqi <= 200) return { label: "Unhealthy", color: "#ef4444", level: 4 };
  return { label: "Very Unhealthy", color: "#a855f7", level: 5 };
}

function buildDemoForecast(cityId: string, horizon: number): ForecastResponse {
  const city = DEMO_CITIES.find((c) => c.id === cityId) || DEMO_CITIES[0];
  const now = new Date();
  now.setMinutes(0, 0, 0);

  const recent_history = Array.from({ length: 24 }, (_, idx) => {
    const t = new Date(now.getTime() - (23 - idx) * 3600 * 1000);
    const wave = Math.sin((t.getHours() - 8) * (Math.PI / 12)) * 18;
    const aqi = Math.max(15, Math.round((city.base_aqi + wave) * 10) / 10);
    return {
      timestamp: t.toISOString(),
      aqi,
      pm25: Math.round(aqi * 0.42 * 10) / 10,
      temperature: 22 + Math.round(Math.sin(idx / 4) * 3 * 10) / 10,
      humidity: 58,
      wind_speed: 8.5,
      traffic_index: 0.55,
    };
  });

  const forecast = Array.from({ length: horizon }, (_, idx) => {
    const h = idx + 1;
    const t = new Date(now.getTime() + h * 3600 * 1000);
    const wave = Math.sin((t.getHours() - 8) * (Math.PI / 12)) * 20;
    const pred = Math.max(15, Math.round((city.base_aqi + wave) * 10) / 10);
    const sigma = 5.2 * Math.sqrt(1 + 0.14 * h);
    return {
      horizon_hour: h,
      timestamp: t.toISOString(),
      predicted_aqi: pred,
      lower_80: Math.max(5, Math.round((pred - 1.28 * sigma) * 10) / 10),
      upper_80: Math.min(500, Math.round((pred + 1.28 * sigma) * 10) / 10),
      lower_95: Math.max(5, Math.round((pred - 1.96 * sigma) * 10) / 10),
      upper_95: Math.min(500, Math.round((pred + 1.96 * sigma) * 10) / 10),
      uncertainty_std: Math.round(sigma * 10) / 10,
      traffic_index: 0.62,
      wind_speed: 8.2,
      temperature: 23.0,
      humidity: 56,
    };
  });

  const peak = Math.max(...forecast.map((f) => f.predicted_aqi));
  const upper95 = Math.max(...forecast.map((f) => f.upper_95));
  const avg = forecast.reduce((s, f) => s + f.predicted_aqi, 0) / forecast.length;
  const currentAqi = recent_history[recent_history.length - 1].aqi;

  return {
    city: { id: city.id, name: city.name, country: city.country },
    current: {
      aqi: currentAqi,
      category: getCategory(currentAqi),
      temperature: 22.4,
      humidity: 58,
      wind_speed: 8.5,
      traffic_index: 0.61,
    },
    horizon_hours: horizon,
    best_model_id: "hist_gbm",
    model_comparisons: [
      { model_id: "persistence", name: "Persistence Baseline", family: "Baseline", mae: 8.42, rmse: 11.15, r2: 0.812, skill_score_vs_persistence: 0.0 },
      { model_id: "ridge", name: "Ridge Regression", family: "Regression", mae: 5.91, rmse: 7.64, r2: 0.911, skill_score_vs_persistence: 0.315 },
      { model_id: "random_forest", name: "Random Forest", family: "Tree Ensemble", mae: 5.48, rmse: 7.12, r2: 0.923, skill_score_vs_persistence: 0.361 },
      { model_id: "hist_gbm", name: "HistGradientBoosting", family: "Tree Ensemble", mae: 5.19, rmse: 6.84, r2: 0.929, skill_score_vs_persistence: 0.387 },
      { model_id: "sarimax", name: "SARIMAX (2,0,1)", family: "Time Series", mae: 6.75, rmse: 8.89, r2: 0.880, skill_score_vs_persistence: 0.203 },
    ],
    feature_drivers: [
      { feature: "aqi_lag_1", label: "AQI (1h ago)", group: "Pollution History", importance: 46.2 },
      { feature: "aqi_roll_mean_6", label: "6h Rolling Mean AQI", group: "Pollution History", importance: 18.4 },
      { feature: "traffic_x_stagnation", label: "Traffic × Stagnation", group: "Traffic Indicators", importance: 9.8 },
      { feature: "wind_speed", label: "Wind Speed (km/h)", group: "Weather", importance: 7.4 },
      { feature: "stagnation_index", label: "Air Stagnation Index", group: "Weather", importance: 5.9 },
      { feature: "traffic_index", label: "Traffic Congestion Index", group: "Traffic Indicators", importance: 4.5 },
      { feature: "hour_sin", label: "Time of Day (sin)", group: "Seasonal & Cyclical", importance: 3.8 },
    ],
    recent_history,
    forecast,
    health_guidance: {
      peak_category: getCategory(peak),
      upper_bound_category: getCategory(upper95),
      average_aqi: Math.round(avg * 10) / 10,
      uncertainty_note: `Forecasts carry inherent atmospheric uncertainty: while the expected peak is ${Math.round(peak)} (${getCategory(peak).label}), the 95% upper bound reaches ${Math.round(upper95)} (${getCategory(upper95).label}).`,
      groups: [
        { group: "Children & Infants", risk: "Elevated", advice: "Limit prolonged outdoor exertion; take frequent indoor breaks." },
        { group: "Older Adults (65+)", risk: "Elevated", advice: "Avoid strenuous outdoor tasks; stay indoors during peak hours." },
        { group: "Asthma & Respiratory", risk: "High", advice: "Move exercise indoors, keep windows closed, and use air purifiers." },
        { group: "Outdoor Athletes", risk: "Elevated", advice: "Shorten outdoor workouts and lower intensity." },
      ],
    },
    is_demo_fallback: true,
  };
}
