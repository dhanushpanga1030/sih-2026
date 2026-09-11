"""ML Model Training Script for SafeHabitat AI.

Trains XGBoost/Random Forest models on real open datasets:
- NRSC/ISRO Flood Hazard Zonation Atlas (1998-2023)
- India Flood Inventory (IFI-Impacts v4): DFSI, flood events, flooded area
- Census 2011: population demographics
- Computed hazard/vulnerability/exposure scores

Models trained:
1. Flood susceptibility (XGBoost) — predicts flood score
2. Landslide susceptibility (Random Forest) — predicts landslide score
3. Vulnerability scoring (XGBoost) — predicts vulnerability composite
4. Risk fusion (XGBoost) — predicts overall risk
5. Priority band classifier (Random Forest) — classifies relocation urgency
"""

import json
import pickle
from pathlib import Path

import numpy as np
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import LabelEncoder

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "assam"
MODEL_DIR = Path(__file__).parent.parent / "models"
MODEL_DIR.mkdir(exist_ok=True)


def load_data():
    fp = DATA_DIR / "assam_data.json"
    return json.loads(fp.read_text())


def prepare_features(data):
    """Extract feature matrix from habitation data using all real datasets.

    Features come from:
    - NRSC satellite data (hazard scores)
    - Census 2011 (vulnerability, population)
    - IFI-Impacts v4 (DFSI, historical floods, flooded area)
    - Computed interaction features
    """
    district_lookup = {d["name"]: d for d in data["districts"]}

    features = []
    for h in data["habitations"]:
        dist = district_lookup.get(h["district"], {})
        nrsc = dist.get("nrsc_flood_data", {})

        # Core hazard scores (NRSC satellite data)
        flood = h["hazard"]["flood"]
        landslide = h["hazard"]["landslide"]
        seismic = h["hazard"]["seismic"]
        erosion = h["hazard"]["erosion"]
        hazard_combined = h["hazard"]["combined"]

        # Vulnerability scores (Census 2011)
        pop_density = h["vulnerability"]["population_density"]
        poverty = h["vulnerability"]["poverty_index"]
        age_vuln = h["vulnerability"]["age_vulnerability"]
        disability = h["vulnerability"]["disability_index"]
        infra = h["vulnerability"]["infrastructure_quality"]
        vuln_combined = h["vulnerability"]["combined"]

        # Exposure and population
        exposure = h["exposure"]
        population = h["population"]
        area = h["area_sq_km"]
        pop_per_sq_km = population / max(area, 0.01)

        # NRSC district enrichment
        nrsc_flood_risk = nrsc.get("flood_risk", flood)
        hazard_index = nrsc.get("hazard_index", 0)
        flood_waves = nrsc.get("flood_waves", 0)
        very_high_villages = nrsc.get("very_high_villages", 0)
        high_villages = nrsc.get("high_villages", 0)
        total_villages = nrsc.get("total_villages", 1)
        flood_village_ratio = (very_high_villages + high_villages) / max(total_villages, 1)

        # IFI-Impacts real datasets
        dfsi = dist.get("dfsi", 0)
        historical_floods = dist.get("historical_flood_events", 0)
        avg_flood_duration = dist.get("avg_flood_duration_days", 0)
        flood_fatalities = dist.get("total_flood_fatalities", 0)
        flooded_area_pct = dist.get("corrected_flooded_area_pct", 0)
        permanent_water = dist.get("permanent_water_pct", 0)

        # Interaction features
        hazard_x_exposure = hazard_combined * exposure
        flood_x_vuln = flood * vuln_combined
        dfsi_x_flood = dfsi * flood / 100  # normalize DFSI

        feat = {
            # Core hazard (NRSC satellite)
            "flood_score": flood,
            "landslide_score": landslide,
            "seismic_score": seismic,
            "erosion_score": erosion,
            "hazard_combined": hazard_combined,
            # Vulnerability (Census 2011)
            "pop_density": pop_density,
            "poverty_index": poverty,
            "age_vulnerability": age_vuln,
            "disability_index": disability,
            "infra_quality": infra,
            "vuln_combined": vuln_combined,
            # Exposure
            "exposure": exposure,
            "population": population,
            "area_sq_km": area,
            "pop_per_sq_km": pop_per_sq_km,
            # NRSC district enrichment
            "nrsc_flood_risk": nrsc_flood_risk,
            "hazard_index": hazard_index,
            "flood_waves": flood_waves,
            "flood_village_ratio": flood_village_ratio,
            # IFI-Impacts real data
            "dfsi": dfsi,
            "historical_floods": historical_floods,
            "avg_flood_duration": avg_flood_duration,
            "flood_fatalities": flood_fatalities,
            "flooded_area_pct": flooded_area_pct,
            "permanent_water": permanent_water,
            # Interaction
            "hazard_x_exposure": hazard_x_exposure,
            "flood_x_vuln": flood_x_vuln,
            "dfsi_x_flood": dfsi_x_flood,
        }
        features.append(feat)
    return features


FEATURE_NAMES = [
    # Core hazard
    "flood_score",
    "landslide_score",
    "seismic_score",
    "erosion_score",
    "hazard_combined",
    # Vulnerability
    "pop_density",
    "poverty_index",
    "age_vulnerability",
    "disability_index",
    "infra_quality",
    "vuln_combined",
    # Exposure
    "exposure",
    "population",
    "area_sq_km",
    "pop_per_sq_km",
    # NRSC enrichment
    "nrsc_flood_risk",
    "hazard_index",
    "flood_waves",
    "flood_village_ratio",
    # IFI-Impacts real data
    "dfsi",
    "historical_floods",
    "avg_flood_duration",
    "flood_fatalities",
    "flooded_area_pct",
    "permanent_water",
    # Interaction
    "hazard_x_exposure",
    "flood_x_vuln",
    "dfsi_x_flood",
]


def train_flood_model(X, y):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = xgb.XGBRegressor(
        n_estimators=150,
        max_depth=6,
        learning_rate=0.08,
        objective="reg:squarederror",
        random_state=42,
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
    preds = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    r2 = r2_score(y_test, preds)
    print(f"  Flood Model      - RMSE: {rmse:.4f}  R2: {r2:.4f}")
    return model


def train_landslide_model(X, y):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=150, max_depth=8, random_state=42)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    r2 = r2_score(y_test, preds)
    print(f"  Landslide Model  - RMSE: {rmse:.4f}  R2: {r2:.4f}")
    return model


def train_vulnerability_model(X, y):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = xgb.XGBRegressor(
        n_estimators=120,
        max_depth=5,
        learning_rate=0.08,
        objective="reg:squarederror",
        random_state=42,
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
    preds = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    r2 = r2_score(y_test, preds)
    print(f"  Vulnerability    - RMSE: {rmse:.4f}  R2: {r2:.4f}")
    return model


def train_risk_model(X, y):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = xgb.XGBRegressor(
        n_estimators=150,
        max_depth=6,
        learning_rate=0.06,
        objective="reg:squarederror",
        random_state=42,
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
    preds = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    r2 = r2_score(y_test, preds)
    print(f"  Risk Fusion      - RMSE: {rmse:.4f}  R2: {r2:.4f}")
    return model


def train_priority_classifier(X, bands):
    le = LabelEncoder()
    y = le.fit_transform(bands)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=150, max_depth=8, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    acc = np.mean(preds == y_test)
    print(f"  Priority Band    - Accuracy: {acc:.4f}")
    print(f"  Classes: {list(le.classes_)}")
    return model, le


def main():
    print("=" * 60)
    print("  SafeHabitat AI - Model Training (Real Open Datasets)")
    print("=" * 60)

    data = load_data()
    features_raw = prepare_features(data)

    X = np.array([[f[k] for k in FEATURE_NAMES] for f in features_raw])

    # Labels from real computed scores
    flood_y = np.array([h["hazard"]["flood"] for h in data["habitations"]])
    landslide_y = np.array([h["hazard"]["landslide"] for h in data["habitations"]])
    vuln_y = np.array([h["vulnerability"]["combined"] for h in data["habitations"]])
    risk_y = np.array([h["risk"]["overall"] for h in data["habitations"]])
    bands = [h["risk"]["band"] for h in data["habitations"]]

    print(f"\n  Habitations: {len(X)}")
    print(f"  Features:    {len(FEATURE_NAMES)}")
    print(f"  Band dist:   {dict(zip(*np.unique(bands, return_counts=True)))}")

    # Count how many have real IFI data
    has_dfsi = sum(1 for f in features_raw if f["dfsi"] > 0)
    has_flood_hist = sum(1 for f in features_raw if f["historical_floods"] > 0)
    print(f"  With DFSI:        {has_dfsi}/{len(features_raw)}")
    print(f"  With flood hist:  {has_flood_hist}/{len(features_raw)}")

    print("\nTraining models...")
    flood_model = train_flood_model(X, flood_y)
    landslide_model = train_landslide_model(X, landslide_y)
    vuln_model = train_vulnerability_model(X, vuln_y)
    risk_model = train_risk_model(X, risk_y)
    priority_model, label_encoder = train_priority_classifier(X, bands)

    # Feature importance for risk model
    importances = sorted(
        zip(FEATURE_NAMES, risk_model.feature_importances_),
        key=lambda x: x[1],
        reverse=True,
    )
    print("\n  Top features (risk model):")
    for name, imp in importances[:10]:
        print(f"    {name:24s} {imp:.4f}")

    # Cross-validation for risk model
    cv_scores = cross_val_score(risk_model, X, risk_y, cv=5, scoring="r2")
    print(f"\n  Risk model 5-fold CV R2: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

    models = {
        "flood_model": flood_model,
        "landslide_model": landslide_model,
        "vulnerability_model": vuln_model,
        "risk_model": risk_model,
        "priority_model": priority_model,
        "label_encoder": label_encoder,
        "feature_names": FEATURE_NAMES,
        "training_stats": {
            "n_habitations": len(X),
            "n_features": len(FEATURE_NAMES),
            "band_distribution": dict(zip(*np.unique(bands, return_counts=True))),
            "data_sources": [
                "NRSC/ISRO Flood Hazard Zonation Atlas (1998-2023)",
                "India Flood Inventory v4 (IFI-Impacts) - DFSI, flood events, flooded area",
                "Census 2011 - population demographics",
            ],
            "features_with_dfsi": has_dfsi,
            "features_with_flood_history": has_flood_hist,
        },
    }

    out = MODEL_DIR / "trained_models.pkl"
    with open(out, "wb") as f:
        pickle.dump(models, f)

    print(f"\n  Saved to {out}")
    print("  Done.")


if __name__ == "__main__":
    main()
