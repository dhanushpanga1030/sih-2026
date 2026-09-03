# SafeHabitat AI — Problem Statement Demo

## Problem Statement 26191
**"Development of AI based Multi hazard Habitability Risk & Relocation Decision Support Platform"**

---

## The Problem (60 seconds)

### Why This Matters
- India faces **3x more flood events** than any other country
- **33 districts** in Assam are flood-affected
- **34.5%** of Assam's geographic area is flood-prone
- **2.7 million hectares** affected annually

### Current Gaps
1. **No real-time risk assessment** — Decisions based on manual surveys
2. **No explainability** — "Why is this village at risk?" → No answer
3. **No relocation planning** — "Where should people move?" → Guesswork
4. **No scenario modeling** — "What if rainfall increases?" → Unknown

---

## Our Solution (90 seconds)

### Layer 1: Data Ingestion
**NRSC/ISRO Satellite Data (1998-2023)**
- 389 multi-sensor datasets (IRS, Radarsat, Sentinel, RISAT, MODIS)
- 50m x 50m spatial resolution
- Flood Hazard Ranking Index (I, II, III)
- Validated against ASDMA field reports (81% match)

### Layer 2: Multi-Hazard Risk Scoring
**Machine Learning Models**
- XGBoost Regressor — flood susceptibility
- Random Forest Regressor — landslide risk
- XGBoost Regressor — vulnerability scoring
- XGBoost Classifier — priority band assignment

**Risk Formula:**
```
Risk = 0.4 × Hazard + 0.3 × Vulnerability + 0.3 × Exposure
```

**Priority Bands:**
| Band | Score | Action |
|------|-------|--------|
| Immediate | ≥ 0.65 | Relocate now |
| Short-Term | ≥ 0.50 | Plan within 6 months |
| Medium-Term | ≥ 0.35 | Plan within 2 years |
| Monitor | < 0.35 | Continue monitoring |

### Layer 3: Explainable AI (SHAP)
- SHAP TreeExplainer shows **exactly** why each village is at risk
- Feature contributions: flood history (+12.8%), population density (+8.2%), slope (+6.4%)
- Not a black box — anyone can see the reasoning

### Layer 4: Relocation Decision Support
- Ranks safe relocation sites by suitability score
- Carrying capacity analysis (current population vs max capacity)
- Infrastructure assessment (water, healthcare, schools, roads)

### Layer 5: Scenario Simulation
- "What if rainfall increases by 20%?"
- See risk scores change in real-time
- Identify villages that cross priority thresholds

---

## Live Demo Flow (3 minutes)

### Step 1: State Overview
**URL:** http://localhost:5173

**Script:**
"This is Assam. 33 districts, 148 habitations, 4.5 million people at risk.
Red dots are immediate relocation needed. Orange is short-term."

**Show:**
- Total habitations: 148
- High risk count: 17
- People at risk: 850,000

### Step 2: Village Risk Breakdown
**Action:** Click a red dot (immediate risk)

**Script:**
"This village has a risk score of 0.72 — immediate relocation priority."

**Show:**
- Hazard scores: flood (0.85), landslide (0.45), seismic (0.30), erosion (0.25)
- Vulnerability scores: population density, poverty, age, disability
- Risk band: Immediate

### Step 3: Explainable AI (SHAP)
**Action:** Scroll to SHAP waterfall chart

**Script:**
"This is explainable AI. Not a black box.
Flood history contributes +12.8%. Population density adds +8.2%.
Anyone can see exactly why this village is at risk."

**Show:**
- Top factors: flood_history, pop_density, slope, river_dist
- Feature contributions with percentages
- Natural language explanation

### Step 4: Relocation Sites
**Action:** Click "Find Relocation Sites"

**Script:**
"The system finds and ranks safe relocation sites.
Site A scores 0.82 — best fit.
Carrying capacity check: Feasible. Current 12,000, Max 50,000."

**Show:**
- Ranked sites with suitability scores
- Infrastructure assessment
- Carrying capacity verdict

### Step 5: Scenario Simulation
**Action:** Click "Scenario" tab → Set rainfall +20% → Run

**Script:**
"What if climate change increases rainfall by 20%?
This village moves from short-term to immediate.
23 villages change priority band.
This is what-if planning — impossible with static maps."

**Show:**
- Risk score changes
- Band transitions
- SHAP factor shifts

### Step 6: Data Source
**Action:** Point to data source badge

**Script:**
"Built on real satellite data: 389 datasets from NRSC/ISRO spanning 26 years.
81% validated against field reports."

---

## Closing (30 seconds)

"SafeHabitat AI solves the problem with:
1. Real satellite data (26 years, 389 datasets)
2. Explainable AI (SHAP — not a black box)
3. Complete decision pipeline (data → risk → relocation)
4. Scenario simulation (what-if planning)
5. Advisory only (respects human authority)

Built for disaster management authorities who need answers, not just numbers."

---

## Backup Slides

### Tech Stack
| Layer | Technology |
|-------|------------|
| Frontend | React, TypeScript, MapLibre GL, Recharts |
| Backend | FastAPI, Python 3.11 |
| ML | XGBoost, Random Forest, SHAP |
| Database | PostGIS, SQLite |
| Monitoring | Prometheus, Grafana |

### Data Sources
- NRSC/ISRO — Flood Hazard Zonation Atlas (1998-2023)
- Census of India — Population data
- OpenStreetMap — Infrastructure
- IMD — Rainfall data
- CWC — River gauge data

### Methodology
- Flood Hazard Formula: `(∑ H x A) x F`
- Risk Score: `0.4 × Hazard + 0.3 × Vulnerability + 0.3 × Exposure`
- Explainability: SHAP TreeExplainer
- Relocation: Multi-criteria decision analysis

### Key URLs
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs
- Swagger: http://localhost:8000/redoc
