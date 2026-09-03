# SafeHabitat AI

**AI-Powered Multi-Hazard Habitation Risk & Relocation Decision Platform**

Built for Smart India Hackathon 2026 — Problem Statement 26191

## What It Does

SafeHabitat AI analyzes multi-hazard risk for habitations in Assam and recommends relocation sites using explainable AI. It processes 26 years of satellite data from NRSC/ISRO to generate risk scores, SHAP-based explanations, and ranked relocation options.

## Key Features

- **Multi-Hazard Risk Scoring** — Flood, landslide, seismic, erosion analysis using XGBoost + Random Forest
- **Explainable AI** — SHAP waterfall charts show exactly why each village is at risk
- **Relocation Ranking** — Finds and ranks safe sites with carrying capacity checks
- **Scenario Simulation** — "What if rainfall increases 20%?" — see risk changes instantly
- **Real Satellite Data** — 389 datasets from NRSC/ISRO (1998-2023), 81% validated
- **Role-Based Access** — Admin, District Officer, Village Analyst roles
- **Monitoring** — Prometheus + Grafana dashboards

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React, TypeScript, MapLibre GL, Recharts, Tailwind CSS |
| Backend | FastAPI, Python 3.11 |
| ML | XGBoost, Random Forest, SHAP TreeExplainer |
| Database | PostGIS (spatial PostgreSQL) |
| Cache | Redis |
| Monitoring | Prometheus, Grafana |
| CI/CD | GitHub Actions, Docker |

## Quick Start

### Development (JSON mode)

```bash
# Backend
cd backend
pip install -r requirements.txt
python -m app.ml.train
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### Production (Docker + PostGIS)

```bash
docker-compose up --build
```

Services:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/state/summary` | Assam-wide risk statistics |
| `GET /api/districts` | List all districts |
| `GET /api/districts/{name}` | District details + habitations |
| `GET /api/habitations` | List habitations (filter by district/band) |
| `GET /api/habitations/{name}` | Habitation details + SHAP + relocation |
| `GET /api/habitations/{name}/explain` | AI explanation for risk score |
| `GET /api/relocation/{habitation}` | Ranked relocation sites |
| `POST /api/scenario` | What-if rainfall simulation |
| `GET /api/data/nrsc` | NRSC satellite data |
| `GET /api/data/sources` | All data sources |
| `GET /api/models/info` | ML model information |

Full API documentation: http://localhost:8000/docs

## Data Sources

- **NRSC/ISRO** — Flood Hazard Zonation Atlas (1998-2023), 389 multi-sensor datasets
- **Census of India** — District population data
- **OpenStreetMap** — Roads, healthcare, schools
- **IMD** — Rainfall climatology
- **CWC** — River gauge data

## Project Structure

```
safehabitat-ai/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── database.py          # PostGIS config
│   │   ├── auth.py              # JWT + RBAC
│   │   ├── cache.py             # Redis caching
│   │   ├── config.py            # Environment config
│   │   ├── routers/api.py       # API endpoints
│   │   ├── engines/             # ML + risk engines
│   │   ├── ml/                  # Model training
│   │   ├── monitoring/          # Prometheus metrics
│   │   ├── ingestion/           # Data pipeline
│   │   └── models/spatial_models.py  # PostGIS schema
│   ├── data/
│   │   └── assam/               # Assam data + generators
│   └── tests/
├── frontend/
│   └── src/
│       ├── components/          # MapView, SHAPWaterfall
│       └── pages/               # Dashboard, District, Village
├── monitoring/                  # Prometheus + Grafana config
├── docker-compose.yml
└── DEMO_SCRIPT.md
```

## Risk Bands

| Band | Score | Action |
|------|-------|--------|
| Immediate | ≥ 0.65 | Relocate now |
| Short-Term | ≥ 0.50 | Plan within 6 months |
| Medium-Term | ≥ 0.35 | Plan within 2 years |
| Monitor | < 0.35 | Continue monitoring |

## Methodology

**Flood Hazard Formula:** `(∑ H x A) x F`
- H = Hazard Zone weightage (1-5)
- A = % Submerged area weightage (1-10)
- F = Flood Wave Index weightage (1-3)

**Risk Score:** `0.4 × Hazard + 0.3 × Vulnerability + 0.3 × Exposure`

## License

MIT
