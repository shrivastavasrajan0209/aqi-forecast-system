"""Rule-based health guidance for sensitive groups with uncertainty-aware messaging."""

from __future__ import annotations


def get_aqi_category(aqi: float) -> dict:
    if aqi <= 50:
        return {"label": "Good", "color": "#10b981", "level": 1}
    if aqi <= 100:
        return {"label": "Moderate", "color": "#f59e0b", "level": 2}
    if aqi <= 150:
        return {"label": "Unhealthy for Sensitive Groups", "color": "#f97316", "level": 3}
    if aqi <= 200:
        return {"label": "Unhealthy", "color": "#ef4444", "level": 4}
    if aqi <= 300:
        return {"label": "Very Unhealthy", "color": "#a855f7", "level": 5}
    return {"label": "Hazardous", "color": "#881337", "level": 6}


def generate_health_guidance(peak_aqi: float, upper_95_peak: float, avg_aqi: float) -> dict:
    """Return rule-based health recommendations for sensitive groups + uncertainty note."""
    cat = get_aqi_category(peak_aqi)
    upper_cat = get_aqi_category(upper_95_peak)

    uncertainty_note = (
        f"Forecasts carry inherent atmospheric uncertainty: while the expected peak is {peak_aqi:.0f} ({cat['label']}), "
        f"the 95% upper bound reaches {upper_95_peak:.0f} ({upper_cat['label']}). "
        "Sensitive individuals should plan around the upper bound when scheduling outdoor activities."
    )

    if peak_aqi <= 50:
        groups = [
            {"group": "Children & Infants", "risk": "Low", "advice": "Safe for all outdoor play and school activities."},
            {"group": "Older Adults (65+)", "risk": "Low", "advice": "Normal outdoor walks and exercise are safe."},
            {"group": "Asthma & Respiratory", "risk": "Low", "advice": "Keep rescue inhaler handy as routine precaution."},
            {"group": "Outdoor Athletes", "risk": "Low", "advice": "Ideal conditions for high-intensity endurance training."},
        ]
    elif peak_aqi <= 100:
        groups = [
            {"group": "Children & Infants", "risk": "Low–Moderate", "advice": "Outdoor play is fine; monitor for unusual coughing."},
            {"group": "Older Adults (65+)", "risk": "Moderate", "advice": "Prefer morning or low-traffic hours for longer walks."},
            {"group": "Asthma & Respiratory", "risk": "Moderate", "advice": "Reduce prolonged exertion near busy roadways."},
            {"group": "Outdoor Athletes", "risk": "Low–Moderate", "advice": "Schedule intense sessions away from rush-hour peaks."},
        ]
    elif peak_aqi <= 150:
        groups = [
            {"group": "Children & Infants", "risk": "Elevated", "advice": "Limit prolonged outdoor exertion; take frequent indoor breaks."},
            {"group": "Older Adults (65+)", "risk": "Elevated", "advice": "Avoid strenuous outdoor tasks; stay indoors during peak hours."},
            {"group": "Asthma & Respiratory", "risk": "High", "advice": "Move exercise indoors, keep windows closed, and use air purifiers."},
            {"group": "Outdoor Athletes", "risk": "Elevated", "advice": "Shorten outdoor workouts and lower intensity."},
        ]
    elif peak_aqi <= 200:
        groups = [
            {"group": "Children & Infants", "risk": "High", "advice": "Keep outdoor recess and sports indoors."},
            {"group": "Older Adults (65+)", "risk": "High", "advice": "Remain indoors with filtered air; wear N95 if travel is essential."},
            {"group": "Asthma & Respiratory", "risk": "Very High", "advice": "Avoid all outdoor exertion; follow asthma action plan closely."},
            {"group": "Outdoor Athletes", "risk": "High", "advice": "Move all training indoors."},
        ]
    else:
        groups = [
            {"group": "Children & Infants", "risk": "Severe", "advice": "Strictly indoors with HEPA filtration."},
            {"group": "Older Adults (65+)", "risk": "Severe", "advice": "Avoid going outside; monitor cardiovascular/respiratory symptoms."},
            {"group": "Asthma & Respiratory", "risk": "Critical", "advice": "Stay indoors, run air purifiers continuously, seek care if symptoms worsen."},
            {"group": "Outdoor Athletes", "risk": "Severe", "advice": "Cancel outdoor training; indoor low-intensity only."},
        ]

    return {
        "peak_category": cat,
        "upper_bound_category": upper_cat,
        "average_aqi": round(avg_aqi, 1),
        "uncertainty_note": uncertainty_note,
        "groups": groups,
    }
