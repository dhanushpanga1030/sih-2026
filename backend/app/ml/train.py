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

        # Real IMD rainfall features (matched to nearest station)
        rr = h.get("real_rainfall", {})
        rainfall_annual = rr.get("rainfall_annual_mm", 0)
        rainfall_max_monthly = rr.get("rainfall_max_monthly_mm", 0)
        rainfall_monsoon = rr.get("rainfall_monsoon_mm", 0)
        rainfall_monsoon_pct = rr.get("rainfall_monsoon_pct", 0)
        river_level = rr.get("river_water_level_max_m", 0)

        # Census 2011 district-level data
        c2011 = dist.get("census_2011", {})
        c2011_edu = c2011.get("education", {})
        c2011_health = c2011.get("health", {})
        c2011_water = c2011.get("water", {})
        c2011_transport = c2011.get("transport", {})
        c2011_comm = c2011.get("communication", {})
        c2011_power = c2011.get("power", {})
        c2011_land = c2011.get("land_use", {})
        c2011_drain = c2011.get("drainage", {})
        c2011_sanit = c2011.get("sanitation", {})
        sex_ratio = c2011.get("sex_ratio", 0)
        sc_pct = c2011.get("total_sc", 0) / max(c2011.get("total_population", 1), 1) * 100
        st_pct = c2011.get("total_st", 0) / max(c2011.get("total_population", 1), 1) * 100

        # Interaction features
        hazard_x_exposure = hazard_combined * exposure
        flood_x_vuln = flood * vuln_combined
        dfsi_x_flood = dfsi * flood / 100  # normalize DFSI
        rainfall_x_flood = rainfall_annual * flood / 3000  # normalize
        rainfall_x_vuln = rainfall_monsoon * vuln_combined / 2000  # normalize

        # Census interaction features
        low_infra_x_flood = (1 - infra) * flood  # poor infrastructure + high flood = high risk
        no_water_x_vuln = (1 - c2011_water.get("pct_tap_water", 50) / 100) * vuln_combined
        no_road_x_flood = (1 - c2011_transport.get("pct_all_weather", 50) / 100) * flood

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
            # Real IMD rainfall
            "rainfall_annual_mm": rainfall_annual,
            "rainfall_max_monthly_mm": rainfall_max_monthly,
            "rainfall_monsoon_mm": rainfall_monsoon,
            "rainfall_monsoon_pct": rainfall_monsoon_pct,
            "river_water_level_max_m": river_level,
            # Census 2011 - Demographics
            "sex_ratio": sex_ratio,
            "sc_pct": sc_pct,
            "st_pct": st_pct,
            # Census 2011 - Education
            "schools_per_village": c2011_edu.get("schools_per_village", 0),
            "total_schools": c2011_edu.get("total_schools", 0),
            # Census 2011 - Health
            "health_facilities_per_village": c2011_health.get("facilities_per_village", 0),
            "total_health_facilities": c2011_health.get("total_facilities", 0),
            # Census 2011 - Water
            "pct_tap_water": c2011_water.get("pct_tap_water", 0),
            "pct_hand_pump": c2011_water.get("pct_hand_pump", 0),
            # Census 2011 - Transport
            "pct_all_weather_road": c2011_transport.get("pct_all_weather", 0),
            "pct_national_hwy": c2011_transport.get("pct_national_hwy", 0),
            # Census 2011 - Communication
            "pct_mobile_coverage": c2011_comm.get("pct_mobile_coverage", 0),
            # Census 2011 - Power
            "pct_power_domestic": c2011_power.get("pct_domestic", 0),
            # Census 2011 - Drainage
            "pct_closed_drainage": c2011_drain.get("pct_closed", 0),
            "pct_no_drainage": c2011_drain.get("pct_none", 0),
            # Census 2011 - Sanitation
            "pct_tsc_covered": c2011_sanit.get("pct_tsc_covered", 0),
            # Census 2011 - Land Use
            "pct_forest": c2011_land.get("pct_forest", 0),
            "pct_agriculture": c2011_land.get("pct_agriculture", 0),
            # Interaction
            "hazard_x_exposure": hazard_x_exposure,
            "flood_x_vuln": flood_x_vuln,
            "dfsi_x_flood": dfsi_x_flood,
            "rainfall_x_flood": rainfall_x_flood,
            "rainfall_x_vuln": rainfall_x_vuln,
            # Census interactions
            "low_infra_x_flood": low_infra_x_flood,
            "no_water_x_vuln": no_water_x_vuln,
            "no_road_x_flood": no_road_x_flood,
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
    "dfsi", "historical_floods", "avg_flood_duration", "flood_fatalities",
    "flooded_area_pct", "permanent_water",
    # Real IMD rainfall
    "rainfall_annual_mm", "rainfall_max_monthly_mm", "rainfall_monsoon_mm",
    "rainfall_monsoon_pct", "river_water_level_max_m",
    # Census 2011 - Demographics
    "sex_ratio", "sc_pct", "st_pct",
    # Census 2011 - Education
    "schools_per_village", "total_schools",
    # Census 2011 - Health
    "health_facilities_per_village", "total_health_facilities",
    # Census 2011 - Water
    "pct_tap_water", "pct_hand_pump",
    # Census 2011 - Transport
    "pct_all_weather_road", "pct_national_hwy",
    # Census 2011 - Communication
    "pct_mobile_coverage",
    # Census 2011 - Power
    "pct_power_domestic",
    # Census 2011 - Drainage
    "pct_closed_drainage", "pct_no_drainage",
    # Census 2011 - Sanitation
    "pct_tsc_covered",
    # Census 2011 - Land Use
    "pct_forest", "pct_agriculture",
    # Interaction
    "hazard_x_exposure", "flood_x_vuln", "dfsi_x_flood",
    "rainfall_x_flood", "rainfall_x_vuln",
    # Census interactions
    "low_infra_x_flood", "no_water_x_vuln", "no_road_x_flood",
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
                "Census 2011 Village Amenities - 26,395 villages, 35 districts",
                "IMD Real Rainfall - Telemetry hourly data (2021-2026), 49 stations",
            ],
            "features_with_dfsi": has_dfsi,
            "features_with_flood_history": has_flood_hist,
            "census_features_added": 17,
            "census_feature_categories": [
                "demographics", "education", "health", "water",
                "transport", "communication", "power", "drainage",
                "sanitation", "land_use",
            ],
        },
    }

    out = MODEL_DIR / "trained_models.pkl"
    with open(out, "wb") as f:
        pickle.dump(models, f)

    print(f"\n  Saved to {out}")
    print("  Done.")


if __name__ == "__main__":
    main()
