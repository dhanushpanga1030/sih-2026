# SafeHabitat AI — Simple Speech

## Opening
"Good morning. I'm [Name] from [College]. We built SafeHabitat AI for Problem Statement 26191."

## The Problem
"India has 3 times more floods than any country. Assam alone has 33 flood-affected districts. But today, when a village needs to relocate, officials use paper maps and guesswork. No data. No AI. No explanation."

## The Solution
"We built SafeHabitat AI — a platform that uses 26 years of satellite data from NRSC/ISRO to predict flood risk and recommend relocation sites."

## How It Works
"First, we ingest 389 satellite datasets. Then XGBoost and Random Forest models calculate risk scores. SHAP explains exactly why each village is at risk — flood history, population, slope. Finally, we rank safe relocation sites with carrying capacity checks."

## Live Demo
"Let me show you."

**[Show map]**
"This is Assam. 148 villages. Red means relocate now. Orange means plan soon."

**[Click a village]**
"This village has 0.72 risk score. Flood history is the top factor — 18 floods in 26 years."

**[Show SHAP]**
"See this chart? Flood history contributes 12.8%. Population density adds 8.2%. Not a black box."

**[Show relocation]**
"The system recommends Site A — best fit. Water, schools, healthcare. Can hold 50,000 people."

**[Show scenario]**
"What if rainfall increases 20%? Risk scores change. 23 villages move to higher priority."

## Closing
"SafeHabitat AI: Real satellite data. Explainable AI. Complete decision pipeline. Built for disaster authorities who need answers, not just numbers."

## Q&A Ready
- **"Why XGBoost?"** — Best for tabular data, fast, explainable with SHAP
- **"Why not neural networks?"** — We need explainability, not just accuracy
- **"How accurate?"** — 81% validated against field reports
- **"Scalable?"** — Yes, PostGIS + Docker, config not redesign
- **"Real data?"** — Yes, NRSC/ISRO, 26 years, 389 datasets

---

**Total time: 3 minutes**
n