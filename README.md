# AeroPulse — 24–72h AQI Forecast & Health Guidance System

A full-stack machine learning application that forecasts a city's Air Quality Index (AQI) for the next **24–72 hours**, communicates **probabilistic forecast uncertainty** (80% and 95% prediction intervals), benchmarks multiple model families against a **persistence baseline**, and provides **rule-based health guidance** for sensitive groups.

## Key Features
- **Feature Engineering (`backend/app/features.py`)**:
  - **Pollution History**: 1h, 3h, 6h, 12h, 24h AQI lags, 6h/24h rolling means, 6h volatility, PM2.5 & NO₂ lags.
  - **Weather**: Temperature, humidity, wind speed, barometric pressure, precipitation, and derived Air Stagnation Index.
  - **Traffic Indicators**: Rush-hour flags, congestion index, and Traffic × Stagnation interaction.
  - **Seasonal & Cyclical**: Sin/cos encodings for hour-of-day and day-of-week, plus weekend indicator.
- **Model Comparison (`backend/app/models.py`)**:
  - **Persistence Baseline** (`AQI(t) = AQI(t-1)`)
  - **Regression**: Ridge Regression
  - **Tree Ensembles**: Random Forest & HistGradientBoosting
  - **Time Series**: SARIMAX `(2, 0, 1)`
  - Evaluates MAE, RMSE, $R^2$, and Skill Score vs. Persistence.
- **Uncertainty Communication**: Horizon-scaled 80% and 95% prediction intervals rendered as shaded ribbons on the interactive forecast chart.
- **Rule-Based Health Guidance (`backend/app/health_advisor.py`)**: Tailored precautions for Children & Infants, Older Adults, Asthma & Respiratory, and Outdoor Athletes, referencing both expected peak and 95% upper-bound AQI.

## Local Development

### 1. Backend (FastAPI)
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate | macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173`.

## Deploying to GitHub
1. Push this repository to GitHub (`main` branch).
2. In **Settings → Pages**, set **Source** to **GitHub Actions**.
3. The included `.github/workflows/deploy.yml` will automatically run `pytest` on the backend, build the React frontend, and deploy to GitHub Pages (with an automatic static preview fallback when no backend URL is configured, or set `VITE_API_BASE_URL` to your hosted FastAPI URL).
