
import { CityInfo, ForecastResponse } from "./types";

const API_BASE = (
  import.meta.env.VITE_API_BASE_URL ||
  "https://aqi-forecast-system.onrender.com"
).replace(/\/$/, "");

async function apiRequest<T>(url: string): Promise<T> {
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(
      `API request failed: ${response.status} ${response.statusText}`
    );
  }

  return response.json() as Promise<T>;
}

export async function fetchCities(): Promise<CityInfo[]> {
  try {
    return await apiRequest<CityInfo[]>(
      `${API_BASE}/api/cities`
    );
  } catch (error) {
    console.error("Unable to fetch cities:", error);
    throw new Error(
      "Unable to connect to the AQI server. Please try again later."
    );
  }
}

export async function fetchForecast(
  cityId: string,
  horizon: number
): Promise<ForecastResponse> {
  try {
    const url =
      `${API_BASE}/api/forecast` +
      `?city_id=${encodeURIComponent(cityId)}` +
      `&horizon=${encodeURIComponent(horizon)}`;

    const data = await apiRequest<ForecastResponse>(url);

    if (data.is_demo_fallback) {
      throw new Error(
        "The server returned demo data instead of a real forecast."
      );
    }

    return data;
  } catch (error) {
    console.error("Unable to fetch AQI forecast:", error);

    throw new Error(
      error instanceof Error
        ? error.message
        : "Unable to load the AQI forecast. Please try again later."
    );
  }
}
