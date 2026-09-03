from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
import json
from pathlib import Path
from app.engines.shap_explainer import explainer
from app.engines.nlg_engine import nlg_engine
from app.engines.relocation_engine import relocation_engine
from app.engines.path_selector import path_selector
from app.cache import cache_response, invalidate_cache

router = APIRouter()

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "assam"
_data = None


# --- Response Models ---
class StateSummary(BaseModel):
    state: str
    total_districts: int
    total_habitations: int
    total_population: int
    high_risk_count: int
    people_at_risk: int
    band_distribution: dict

    class Config:
        json_schema_extra = {
            "example": {
                "state": "Assam",
                "total_districts": 33,
                "total_habitations": 148,
                "total_population": 4500000,
                "high_risk_count": 17,
                "people_at_risk": 850000,
                "band_distribution": {
                    "immediate": 17,
                    "short_term": 81,
                    "medium_term": 48,
                    "monitor": 2,
                },
            }
        }


class HabitationResponse(BaseModel):
    name: str
    district: str
    population: int
    risk_score: float
    risk_band: str
    lat: float
    lon: float

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Kamrup Village",
                "district": "Kamrup Metropolitan",
                "population": 1500,
                "risk_score": 0.72,
                "risk_band": "immediate",
                "lat": 26.14,
                "lon": 91.74,
            }
        }


class ScenarioRequest(BaseModel):
    rainfall_delta: float = 20.0
    habitation: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "rainfall_delta": 20.0,
                "habitation": "Kamrup Village",
            }
        }


class ExplanationResponse(BaseModel):
    habitation: str
    risk_band: str
    risk_score: float
    confidence: float
    shap_contributions: dict = {}
    top_factors: list = []
    explanation: str
    disclaimer: str
    model_info: dict


def load_data():
    global _data
    if _data is None:
        fp = DATA_DIR / "assam_data.json"
        if not fp.exists():
            raise HTTPException(500, "Data not generated. Run generate_assam_data.py first.")
        _data = json.loads(fp.read_text())
    return _data


def habitation_to_features(h: dict) -> dict:
    """Convert habitation data to ML feature vector matching trained model's 28 features."""
    haz = h.get("hazard", {})
    vuln = h.get("vulnerability", {})
    flood_risk = haz.get("flood", 0)
    vuln_combined = vuln.get("combined", 0)
    exposure = h.get("exposure", 0)
    dfsi = h.get("dfsi", 12)
    pop = h.get("population", 1000)
    area = max(h.get("area_sq_km", 1), 0.01)

    return {
        "flood_score": flood_risk,
        "landslide_score": haz.get("landslide", 0.2),
        "seismic_score": haz.get("seismic", 0.5),
        "erosion_score": haz.get("erosion", 0.2),
        "hazard_combined": haz.get("combined", 0),
        "pop_density": vuln.get("population_density", pop / area),
        "poverty_index": vuln.get("poverty_index", 0.3),
        "age_vulnerability": vuln.get("age_vulnerability", 0.2),
        "disability_index": vuln.get("disability_index", 0.1),
        "infra_quality": vuln.get("infrastructure_quality", 0.5),
        "vuln_combined": vuln_combined,
        "exposure": exposure,
        "population": pop,
        "area_sq_km": area,
        "pop_per_sq_km": pop / area,
        "nrsc_flood_risk": flood_risk,
        "hazard_index": haz.get("hazard_index", 15),
        "flood_waves": haz.get("flood_waves", 15),
        "flood_village_ratio": flood_risk * 0.8,
        "dfsi": dfsi,
        "historical_floods": h.get("historical_flood_events", 10),
        "avg_flood_duration": h.get("avg_flood_duration_days", 1.5),
        "flood_fatalities": h.get("total_flood_fatalities", 5),
        "flooded_area_pct": h.get("corrected_flooded_area_pct", 5),
        "permanent_water": h.get("permanent_water_pct", 1),
        "hazard_x_exposure": haz.get("combined", 0) * exposure,
        "flood_x_vuln": flood_risk * vuln_combined,
        "dfsi_x_flood": dfsi * flood_risk,
    }


@router.get("/state/summary", response_model=StateSummary, tags=["State Overview"])
@cache_response(ttl=600, prefix="state")
def state_summary():
    """Get Assam-wide risk summary and statistics.

    Returns total districts, habitations, population at risk,
    and distribution across priority bands.
    """
    data = load_data()
    habitations = data["habitations"]
    total_pop = sum(h["population"] for h in habitations)
    high_risk = [h for h in habitations if h["risk"]["band"] == "immediate"]
    return {
        "state": "Assam",
        "total_districts": len(data["districts"]),
        "total_habitations": len(habitations),
        "total_population": total_pop,
        "high_risk_count": len(high_risk),
        "people_at_risk": sum(h["population"] for h in high_risk),
        "band_distribution": {
            "immediate": len([h for h in habitations if h["risk"]["band"] == "immediate"]),
            "short_term": len([h for h in habitations if h["risk"]["band"] == "short_term"]),
            "medium_term": len([h for h in habitations if h["risk"]["band"] == "medium_term"]),
            "monitor": len([h for h in habitations if h["risk"]["band"] == "monitor"]),
        },
    }


@router.get("/districts", tags=["Districts"])
@cache_response(ttl=300, prefix="districts")
def list_districts():
    """List all districts in Assam with their basic information."""
    data = load_data()
    return data["districts"]


@router.get("/districts/{name}", tags=["Districts"])
@cache_response(ttl=300, prefix="district")
def get_district(name: str):
    """Get detailed information about a specific district.

    Includes all habitations sorted by risk score, total population,
    and count of high-risk habitations.
    """
    data = load_data()
    for d in data["districts"]:
        if d["name"].lower() == name.lower():
            habitations = [h for h in data["habitations"] if h["district"] == d["name"]]
            return {
                **d,
                "habitations": sorted(habitations, key=lambda x: x["risk"]["overall"], reverse=True),
                "total_population": sum(h["population"] for h in habitations),
                "high_risk_count": len([h for h in habitations if h["risk"]["band"] == "immediate"]),
            }
    raise HTTPException(404, f"District '{name}' not found")


@router.get("/habitations", tags=["Habitations"])
@cache_response(ttl=300, prefix="habitations")
def list_habitations(
    district: Optional[str] = Query(None, description="Filter by district name"),
    band: Optional[str] = Query(None, description="Filter by risk band: immediate, short_term, medium_term, monitor"),
):
    """List all habitations with optional filtering.

    Returns habitations sorted by risk score (highest first).
    Filter by district or risk band to narrow results.
    """
    data = load_data()
    hab = data["habitations"]
    if district:
        hab = [h for h in hab if h["district"].lower() == district.lower()]
    if band:
        hab = [h for h in hab if h["risk"]["band"] == band]
    return sorted(hab, key=lambda x: x["risk"]["overall"], reverse=True)


@router.get("/habitations/{name}", tags=["Habitations"])
@cache_response(ttl=300, prefix="habitation")
def get_habitation(name: str):
    """Get detailed information about a specific habitation.

    Includes ML features, SHAP explanation, and ranked relocation sites.
    """
    data = load_data()
    for h in data["habitations"]:
        if h["name"].lower() == name.lower():
            sites = [s for s in data["relocation_sites"] if s["habitation"] == h["name"]]
            ranked_sites = relocation_engine.rank_sites(h, sites)

            features = habitation_to_features(h)
            shap_data = explainer.explain_risk(features)

            return {
                **h,
                "ml_features": features,
                "shap_explanation": shap_data,
                "relocation_sites": ranked_sites,
            }
    raise HTTPException(404, f"Habitation '{name}' not found")


@router.get("/habitations/{name}/explain", response_model=ExplanationResponse, tags=["Explainability"])
def explain_habitation(name: str):
    """Get AI explanation for a habitation's risk score.

    Returns SHAP feature contributions and natural language explanation
    of why the habitation received its risk score.
    """
    data = load_data()
    for h in data["habitations"]:
        if h["name"].lower() == name.lower():
            features = habitation_to_features(h)
            shap_data = explainer.explain_risk(features)
            explanation_text = nlg_engine.explain_risk(h, h["risk"], shap_data)

            return {
                "habitation": h["name"],
                "risk_band": h["risk"]["band"],
                "risk_score": h["risk"]["overall"],
                "confidence": h["risk"]["confidence"],
                "shap_contributions": shap_data.get("contributions", {}),
                "top_factors": shap_data.get("top_factors", []),
                "explanation": explanation_text,
                "disclaimer": "This is an AI-generated recommendation. Final relocation decisions rest with authorized officials.",
                "model_info": {
                    "risk_model": "XGBoost Regressor",
                    "explainability": "SHAP TreeExplainer",
                    "method": shap_data.get("method", "shap"),
                },
            }
    raise HTTPException(404, f"Habitation '{name}' not found")


@router.get("/relocation/{habitation_name}", tags=["Relocation"])
def relocation_sites(habitation_name: str):
    """Get ranked relocation sites for a habitation.

    Returns sites sorted by suitability score with carrying capacity analysis.
    """
    data = load_data()
    hab = None
    for h in data["habitations"]:
        if h["name"].lower() == habitation_name.lower():
            hab = h
            break

    if not hab:
        raise HTTPException(404, f"Habitation '{habitation_name}' not found")

    sites = [s for s in data["relocation_sites"] if s["habitation"] == hab["name"]]
    ranked = relocation_engine.rank_sites(hab, sites)
    return ranked


@router.get("/relocation/{habitation_name}/explain/{site_name}", tags=["Relocation"])
def explain_site_selection(habitation_name: str, site_name: str):
    """Get explanation for why a specific relocation site was recommended."""
    data = load_data()
    hab = None
    for h in data["habitations"]:
        if h["name"].lower() == habitation_name.lower():
            hab = h
            break

    if not hab:
        raise HTTPException(404, f"Habitation '{habitation_name}' not found")

    sites = [s for s in data["relocation_sites"] if s["habitation"] == hab["name"]]
    ranked = relocation_engine.rank_sites(hab, sites)

    for site in ranked:
        if site["name"].lower() == site_name.lower():
            explanation = nlg_engine.explain_site_selection(site, hab)
            return {
                "site": site,
                "explanation": explanation,
                "disclaimer": "This is an AI-generated recommendation. Final relocation decisions rest with authorized officials.",
            }

    raise HTTPException(404, f"Site '{site_name}' not found")


@router.post("/scenario", tags=["Scenario"])
def scenario_simulation(params: ScenarioRequest):
    """Simulate what-if scenarios for rainfall changes.

    Adjust rainfall_delta (percentage change) to see how risk scores
    and priority bands change across habitations.
    """
    data = load_data()
    rainfall_delta = params.rainfall_delta
    target = params.habitation

    results = []
    for h in data["habitations"]:
        if target and h["name"].lower() != target.lower():
            continue

        old_flood = h["hazard"]["flood"]
        new_flood = min(1.0, old_flood * (1 + rainfall_delta * 0.01))
        old_combined = h["hazard"]["combined"]
        new_combined = round(0.35 * new_flood + 0.25 * h["hazard"]["landslide"] +
                           0.25 * h["hazard"]["seismic"] + 0.15 * h["hazard"]["erosion"], 2)

        old_risk = h["risk"]["overall"]
        new_risk = round(0.4 * new_combined + 0.3 * h["vulnerability"]["combined"] + 0.3 * h["exposure"], 2)

        if new_risk >= 0.65:
            new_band = "immediate"
        elif new_risk >= 0.50:
            new_band = "short_term"
        elif new_risk >= 0.35:
            new_band = "medium_term"
        else:
            new_band = "monitor"

        features = habitation_to_features(h)
        features["flood_history"] = new_flood
        shap_data = explainer.explain_risk(features)

        results.append({
            "habitation": h["name"],
            "district": h["district"],
            "original": {
                "flood_score": old_flood,
                "hazard_score": old_combined,
                "risk_score": old_risk,
                "band": h["risk"]["band"],
            },
            "simulated": {
                "flood_score": round(new_flood, 2),
                "hazard_score": new_combined,
                "risk_score": new_risk,
                "band": new_band,
            },
            "risk_change": round(new_risk - old_risk, 3),
            "band_changed": h["risk"]["band"] != new_band,
            "shap_factors": shap_data.get("top_factors", []),
        })

    results.sort(key=lambda x: x["risk_change"], reverse=True)
    return {"scenario": params.dict(), "results": results}


@router.get("/map/habitations", tags=["Map"])
def map_habitations():
    """Get all habitations for map visualization.

    Returns coordinates, risk scores, and bands for map markers.
    """
    data = load_data()
    return [
        {
            "name": h["name"],
            "district": h["district"],
            "lat": h["lat"],
            "lon": h["lon"],
            "risk_score": h["risk"]["overall"],
            "band": h["risk"]["band"],
            "population": h["population"],
        }
        for h in data["habitations"]
    ]


@router.get("/map/relocation", tags=["Map"])
def map_relocation_sites():
    """Get all relocation sites for map visualization."""
    data = load_data()
    return [
        {
            "name": s["name"],
            "habitation": s["habitation"],
            "lat": s["lat"],
            "lon": s["lon"],
            "suitability": s["suitability_score"],
            "capacity": s["max_capacity"],
        }
        for s in data["relocation_sites"]
    ]


@router.get("/models/info")
def model_info():
    """Return information about trained ML models."""
    from pathlib import Path
    model_path = Path(__file__).parent.parent / "models" / "trained_models.pkl"
    if model_path.exists():
        import pickle
        with open(model_path, "rb") as f:
            models = pickle.load(f)
        return {
            "models_trained": True,
            "models": list(models.keys()),
            "features": models.get("feature_names", []),
            "trained_on": "Synthetic Assam data (148 habitations)",
        }
    return {"models_trained": False, "message": "Run train.py to train models"}


@router.get("/data/nrsc")
def nrsc_flood_data():
    """Return NRSC/ISRO flood hazard zonation data."""
    data = load_data()
    return {
        "metadata": data.get("nrsc_metadata", {}),
        "districts": {
            d["name"]: d.get("nrsc_flood_data", {})
            for d in data["districts"]
        },
    }


@router.get("/data/sources")
def data_sources():
    """Return all data sources used in the system."""
    return {
        "flood_hazard": {
            "source": "NRSC/ISRO Flood Hazard Zonation Atlas of Assam",
            "period": "1998-2023",
            "satellites": "389 multi-sensor datasets (IRS, Radarsat, Sentinel, RISAT, MODIS)",
            "resolution": "50m x 50m",
            "validation": "81% match with field reports (ASDMA)",
            "url": "https://bhuvan.nrsc.gov.in",
        },
        "population": {
            "source": "Census of India",
            "note": "District-level population data",
        },
        "infrastructure": {
            "source": "OpenStreetMap",
            "note": "Roads, healthcare, schools",
        },
        "methodology": {
            "flood_hazard_formula": "(∑ H x A) x F",
            "H": "Hazard Zone weightage (1-5)",
            "A": "% Submerged area weightage (1-10)",
            "F": "Flood Wave Index weightage (1-3)",
            "ranking": "I (>=40), II (20-39), III (1-19)",
        },
    }


@router.get("/evacuation/{habitation_name}", tags=["Evacuation"])
def evacuation_routes(habitation_name: str):
    """Get safe evacuation routes from a red-zone habitation to all ranked relocation sites.

    Returns routes with distance, duration, safety assessment, and logistics.
    """
    data = load_data()
    hab = None
    for h in data["habitations"]:
        if h["name"].lower() == habitation_name.lower():
            hab = h
            break

    if not hab:
        raise HTTPException(404, f"Habitation '{habitation_name}' not found")

    sites = [s for s in data["relocation_sites"] if s["habitation"] == hab["name"]]
    ranked = relocation_engine.rank_sites(hab, sites)

    routes = []
    for site in ranked:
        origin = {"lat": hab["lat"], "lon": hab["lon"]}
        dest = {"lat": site["lat"], "lon": site["lon"]}
        route = path_selector.get_route(origin, dest)
        safety = path_selector.check_road_safety(route.get("geometry", {})) if route.get("status") == "success" else {}

        population = hab.get("population", 0)
        buses_needed = max(1, population // 50)
        trips_needed = max(1, buses_needed // 3)

        routes.append({
            "site": site["name"],
            "suitability_score": site["suitability_score"],
            "carrying_capacity": site.get("carrying_capacity", {}),
            "route": route,
            "safety": safety,
            "logistics": {
                "population": population,
                "buses_needed": buses_needed,
                "trips_needed": trips_needed,
                "total_distance_km": round(route.get("distance_km", 0) * trips_needed, 2) if route.get("status") == "success" else 0,
                "estimated_hours": round(route.get("duration_hours", 0) * trips_needed, 1) if route.get("status") == "success" else 0,
            },
        })

    routes.sort(key=lambda x: x["suitability_score"], reverse=True)

    return {
        "habitation": hab["name"],
        "risk_band": hab["risk"]["band"],
        "risk_score": hab["risk"]["overall"],
        "population": hab.get("population", 0),
        "origin": {"lat": hab["lat"], "lon": hab["lon"]},
        "routes": routes,
    }


@router.get("/evacuation/{habitation_name}/routes/{site_name}", tags=["Evacuation"])
def evacuation_route_detail(habitation_name: str, site_name: str):
    """Get detailed route with turn-by-turn directions for a specific relocation site."""
    data = load_data()
    hab = None
    for h in data["habitations"]:
        if h["name"].lower() == habitation_name.lower():
            hab = h
            break

    if not hab:
        raise HTTPException(404, f"Habitation '{habitation_name}' not found")

    site = None
    for s in data["relocation_sites"]:
        if s["habitation"] == hab["name"] and s["name"].lower() == site_name.lower():
            site = s
            break

    if not site:
        raise HTTPException(404, f"Site '{site_name}' not found for habitation '{habitation_name}'")

    origin = {"lat": hab["lat"], "lon": hab["lon"]}
    dest = {"lat": site["lat"], "lon": site["lon"]}

    route = path_selector.get_route(origin, dest)
    routes_alt = path_selector.find_multiple_routes(origin, dest)
    safety = path_selector.check_road_safety(route.get("geometry", {})) if route.get("status") == "success" else {}
    evacuation_plan = path_selector.plan_evacuation(hab, site)

    return {
        "habitation": hab["name"],
        "site": site["name"],
        "origin": origin,
        "destination": dest,
        "primary_route": route,
        "alternative_routes": routes_alt,
        "safety": safety,
        "evacuation_plan": evacuation_plan,
    }


@router.get("/cache/stats", tags=["Monitoring"])
def cache_stats():
    """Get Redis cache hit/miss statistics."""
    from app.cache import cache_stats as get_cache_stats
    return get_cache_stats()


@router.post("/cache/invalidate", tags=["Monitoring"])
def invalidate_cache_endpoint(pattern: str = "api:*"):
    """Invalidate cache entries matching pattern."""
    from app.cache import invalidate_cache
    invalidate_cache(pattern)
    return {"status": "invalidated", "pattern": pattern}
