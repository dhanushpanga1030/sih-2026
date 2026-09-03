# SafeHabitat AI — Demo Script (3 minutes)

## Opening (15 seconds)
"India faces 3x more flood events than any other country. 33 districts in Assam are affected. But today, relocation decisions are made manually, without data. SafeHabitat AI changes that."

## 1. State Overview (30 seconds)
**Action:** Open http://localhost:5173 → State Dashboard

"Here's Assam. 33 districts, 148 habitations, 4.5 million people at risk."

**Point to map:** "Red dots are immediate relocation needed. Orange is short-term. Yellow is medium-term."

**Click on a red dot:** "Let's look at this high-risk village."

## 2. Village Risk Breakdown (45 seconds)
**Action:** Click a high-risk habitation → Habitation Detail page

"This village has a risk score of 0.72 — immediate relocation priority."

**Scroll to SHAP chart:** "This is explainable AI. Not a black box."

**Point to bars:** "Flood history contributes +12.8%. Population density adds +8.2%. Slope adds +6.4%."

"Anyone can see exactly why this village is at risk."

## 3. AI Explanation (30 seconds)
**Action:** Click "Why?" button → Explanation panel

"The system generates a natural language explanation:"

**Read:** "'This village has high flood risk due to proximity to river Brahmaputra, low elevation, and dense population. Historical flood data shows 18 flood events in 26 years.'"

**Point to disclaimer:** "Note: This is an AI recommendation. Final decision rests with authorized officials."

## 4. Relocation Sites (30 seconds)
**Action:** Click "Find Relocation Sites" → Relocation tab

"The system finds and ranks safe relocation sites."

**Point to ranking:** "Site A scores 0.82 — best fit. It has water, schools, healthcare, and can hold 50,000 people."

**Point to carrying capacity:** "Carrying capacity check: Feasible. Current population 12,000. Max capacity 50,000."

## 5. Scenario Simulation (30 seconds)
**Action:** Click "Scenario" tab → Set rainfall +20%

"What if climate change increases rainfall by 20%?"

**Click Run:** "Watch the risk scores change."

**Point to results:** "This village moves from short-term to immediate. 23 villages change priority band."

"This is what-if planning — impossible with static maps."

## 6. Data Source (15 seconds)
**Action:** Scroll to data source badge

"Built on real satellite data: 389 datasets from NRSC/ISRO spanning 26 years. 81% validated against field reports."

## Closing (15 seconds)
"SafeHabitat AI: Real data, explainable AI, and a complete decision pipeline. Built for disaster management authorities who need answers, not just numbers."

---

## Key URLs
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs
- State Dashboard: http://localhost:5173
- District View: http://localhost:5173 → Click a district
- Habitation Detail: Click any village marker

## Backup Talking Points
- "26 years of satellite data" — judges love real data
- "Explainable AI with SHAP" — not a black box
- "Advisory only" — respects human authority
- "End-to-end" — from data to decision
- "Scales with config" — demo on one district, deploy to full state
