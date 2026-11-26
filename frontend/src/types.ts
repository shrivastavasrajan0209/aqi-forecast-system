export interface CityInfo {
  id: string;
  name: string;
  country: string;
  base_aqi: number;
}

export interface AqiCategory {
  label: string;
  color: string;
  level: number;
}

export interface ForecastPoint {
  horizon_hour: number;
  timestamp: string;
  predicted_aqi: number;
  lower_80: number;
  upper_80: number;
  lower_95: number;
  upper_95: number;
  uncertainty_std: number;
  traffic_index: number;
  wind_speed: number;
  temperature: number;
  humidity: number;
}

export interface HistoryPoint {
  timestamp: string;
  aqi: number;
  pm25: number;
  temperature: number;
  humidity: number;
  wind_speed: number;
  traffic_index: number;
}

export interface ModelComparison {
  model_id: string;
  name: string;
  family: string;
  mae: number;
  rmse: number;
  r2: number;
  skill_score_vs_persistence: number;
}

export interface FeatureDriver {
  feature: string;
  label: string;
  group: string;
  importance: number;
}

export interface HealthGroupAdvice {
  group: string;
  risk: string;
  advice: string;
}

export interface HealthGuidance {
  peak_category: AqiCategory;
  upper_bound_category: AqiCategory;
  average_aqi: number;
  uncertainty_note: string;
  groups: HealthGroupAdvice[];
}

export interface ForecastResponse {
  city: { id: string; name: string; country: string };
  current: {
    aqi: number;
    category: AqiCategory;
    temperature: number;
    humidity: number;
    wind_speed: number;
    traffic_index: number;
  };
  horizon_hours: number;
  best_model_id: string;
  model_comparisons: ModelComparison[];
  feature_drivers: FeatureDriver[];
  recent_history: HistoryPoint[];
  forecast: ForecastPoint[];
  health_guidance: HealthGuidance;
  is_demo_fallback?: boolean;
}
