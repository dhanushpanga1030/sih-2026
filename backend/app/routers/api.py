import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.engines.shap_explainer import explainer
from app.engines.nlg_engine import nlg_engine
from app.engines.relocation_engine import relocation_engine
from app.engines.drie_engine import drie_engine
from app.engines.matching_engine import matching_engine
from app.engines.route_intelligence import route_intelligence_engine
from app.engines.multi_hazard_sim import multi_hazard_simulator
from app.engines.household_vulnerability import household_vulnerability_engine
from app.engines.report_generator import report_generator
from app.workflow.state_machine import workflow_manager
from app.cache import cache_response, invalidate_cache
from app.engines.path_selector import path_selector
from app.routers.auth_router import require_role

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
    habitation: str | None = None
    seismic_magnitude: float = 0
    landslide_trigger: float = 0
    river_level_rise: float = 0
    embankment_breach: bool = False
    population_growth_pct: float = 0

    class Config:
        json_schema_extra = {
            "example": {
                "rainfall_delta": 20.0,
                "habitation": "Kamrup Village",
                "seismic_magnitude": 0,
                "landslide_trigger": 0,
                "river_level_rise": 0,
                "embankment_breach": False,
                "population_growth_pct": 0,
            }
        }


class WorkflowTransitionRequest(BaseModel):
    item_id: str
    new_state: str
    actor: str = "system"
    note: str = ""


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


def _find_district(data: dict, district_name: str) -> dict | None:
    for d in data["districts"]:
        if d["name"].lower() == district_name.lower():
            return d
    return None


def habitation_to_features(h: dict, dist: dict = None) -> dict:
    """Convert habitation data to ML feature vector matching trained model's 56 features."""
    haz = h.get("hazard", {})
    vuln = h.get("vulnerability", {})
    flood_risk = haz.get("flood", 0)
    vuln_combined = vuln.get("combined", 0)
    exposure = h.get("exposure", 0)
    dfsi = h.get("dfsi", 12)
    pop = h.get("population", 1000)
    area = max(h.get("area_sq_km", 1), 0.01)
    infra = vuln.get("infrastructure_quality", 0.5)

    rr = h.get("real_rainfall", {})
    rainfall_annual = rr.get("rainfall_annual_mm", 0)
    rainfall_monsoon = rr.get("rainfall_monsoon_mm", 0)

    # Census 2011 data
    c = (dist or {}).get("census_2011", {})
    ce = c.get("education", {})
    ch = c.get("health", {})
    cw = c.get("water", {})
    ct = c.get("transport", {})
    cc = c.get("communication", {})
    cp = c.get("power", {})
    cd = c.get("drainage", {})
    cs = c.get("sanitation", {})
    cl = c.get("land_use", {})
    sc_pct = c.get("total_sc", 0) / max(c.get("total_population", 1), 1) * 100
    st_pct = c.get("total_st", 0) / max(c.get("total_population", 1), 1) * 100

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
        "infra_quality": infra,
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
        "rainfall_annual_mm": rainfall_annual,
        "rainfall_max_monthly_mm": rr.get("rainfall_max_monthly_mm", 0),
        "rainfall_monsoon_mm": rainfall_monsoon,
        "rainfall_monsoon_pct": rr.get("rainfall_monsoon_pct", 0),
        "river_water_level_max_m": rr.get("river_water_level_max_m", 0),
        # Census 2011
        "sex_ratio": c.get("sex_ratio", 0),
        "sc_pct": sc_pct,
        "st_pct": st_pct,
        "schools_per_village": ce.get("schools_per_village", 0),
        "total_schools": ce.get("total_schools", 0),
        "health_facilities_per_village": ch.get("facilities_per_village", 0),
        "total_health_facilities": ch.get("total_facilities", 0),
        "pct_tap_water": cw.get("pct_tap_water", 0),
        "pct_hand_pump": cw.get("pct_hand_pump", 0),
        "pct_all_weather_road": ct.get("pct_all_weather", 0),
        "pct_national_hwy": ct.get("pct_national_hwy", 0),
        "pct_mobile_coverage": cc.get("pct_mobile_coverage", 0),
        "pct_power_domestic": cp.get("pct_domestic", 0),
        "pct_closed_drainage": cd.get("pct_closed", 0),
        "pct_no_drainage": cd.get("pct_none", 0),
        "pct_tsc_covered": cs.get("pct_tsc_covered", 0),
        "pct_forest": cl.get("pct_forest", 0),
        "pct_agriculture": cl.get("pct_agriculture", 0),
        # Interaction
        "hazard_x_exposure": haz.get("combined", 0) * exposure,
        "flood_x_vuln": flood_risk * vuln_combined,
        "dfsi_x_flood": dfsi * flood_risk,
        "rainfall_x_flood": rainfall_annual * flood_risk / 3000,
        "rainfall_x_vuln": rainfall_monsoon * vuln_combined / 2000,
        "low_infra_x_flood": (1 - infra) * flood_risk,
        "no_water_x_vuln": (1 - cw.get("pct_tap_water", 50) / 100) * vuln_combined,
        "no_road_x_flood": (1 - ct.get("pct_all_weather", 50) / 100) * flood_risk,
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
                "habitations": sorted(
                    habitations, key=lambda x: x["risk"]["overall"], reverse=True
                ),
                "total_population": sum(h["population"] for h in habitations),
                "high_risk_count": len(
                    [h for h in habitations if h["risk"]["band"] == "immediate"]
                ),
            }
    raise HTTPException(404, f"District '{name}' not found")


@router.get("/habitations", tags=["Habitations"])
@cache_response(ttl=300, prefix="habitations")
def list_habitations(
    district: str | None = Query(None, description="Filter by district name"),
    band: str | None = Query(
        None, description="Filter by risk band: immediate, short_term, medium_term, monitor"
    ),
    limit: int | None = Query(None, description="Limit number of results"),
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
    hab = sorted(hab, key=lambda x: x["risk"]["overall"], reverse=True)
    if limit:
        hab = hab[:limit]
    return hab


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

            dist = _find_district(data, h["district"])
            features = habitation_to_features(h, dist)
            shap_data = explainer.explain_risk(features)

            return {
                **h,
                "ml_features": features,
                "shap_explanation": shap_data,
                "relocation_sites": ranked_sites,
                "census_2011": dist.get("census_2011", {}) if dist else {},
            }
    raise HTTPException(404, f"Habitation '{name}' not found")


@router.get(
    "/habitations/{name}/explain", response_model=ExplanationResponse, tags=["Explainability"]
)
def explain_habitation(name: str):
    """Get AI explanation for a habitation's risk score.

    Returns SHAP feature contributions and natural language explanation
    of why the habitation received its risk score.
    """
    data = load_data()
    for h in data["habitations"]:
        if h["name"].lower() == name.lower():
            dist = _find_district(data, h["district"])
            features = habitation_to_features(h, dist)
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
                "census_2011": dist.get("census_2011", {}) if dist else {},
            }
    raise HTTPException(404, f"Habitation '{name}' not found")


@router.get("/census/{district_name}", tags=["Census 2011"])
@cache_response(ttl=600, prefix="census")
def get_census(district_name: str):
    """Get Census 2011 data for a district — demographics, education, health, water, transport, power."""
    data = load_data()
    dist = _find_district(data, district_name)
    if not dist:
        raise HTTPException(404, f"District '{district_name}' not found")
    return {
        "district": dist["name"],
        "census_2011": dist.get("census_2011", {}),
    }


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
def scenario_simulation(
    params: ScenarioRequest,
    user: dict = Depends(require_role("admin", "village_analyst")),
):
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
        new_combined = round(
            0.35 * new_flood
            + 0.25 * h["hazard"]["landslide"]
            + 0.25 * h["hazard"]["seismic"]
            + 0.15 * h["hazard"]["erosion"],
            2,
        )

        old_risk = h["risk"]["overall"]
        new_risk = round(
            0.4 * new_combined + 0.3 * h["vulnerability"]["combined"] + 0.3 * h["exposure"], 2
        )

        if new_risk >= 0.65:
            new_band = "immediate"
        elif new_risk >= 0.50:
            new_band = "short_term"
        elif new_risk >= 0.35:
            new_band = "medium_term"
        else:
            new_band = "monitor"

        dist = _find_district(data, h["district"])
        features = habitation_to_features(h, dist)
        features["flood_history"] = new_flood
        shap_data = explainer.explain_risk(features)

        results.append(
            {
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
            }
        )

    results.sort(key=lambda x: x["risk_change"], reverse=True)
    return {"scenario": params.model_dump(), "results": results}


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
        "districts": {d["name"]: d.get("nrsc_flood_data", {}) for d in data["districts"]},
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
        safety = (
            path_selector.check_road_safety(route.get("geometry", {}))
            if route.get("status") == "success"
            else {}
        )

        population = hab.get("population", 0)
        buses_needed = max(1, population // 50)
        trips_needed = max(1, buses_needed // 3)

        routes.append(
            {
                "site": site["name"],
                "suitability_score": site["suitability_score"],
                "carrying_capacity": site.get("carrying_capacity", {}),
                "route": route,
                "safety": safety,
                "logistics": {
                    "population": population,
                    "buses_needed": buses_needed,
                    "trips_needed": trips_needed,
                    "total_distance_km": round(route.get("distance_km", 0) * trips_needed, 2)
                    if route.get("status") == "success"
                    else 0,
                    "estimated_hours": round(route.get("duration_hours", 0) * trips_needed, 1)
                    if route.get("status") == "success"
                    else 0,
                },
            }
        )

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
    safety = (
        path_selector.check_road_safety(route.get("geometry", {}))
        if route.get("status") == "success"
        else {}
    )
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
def invalidate_cache_endpoint(
    pattern: str = "api:*",
    user: dict = Depends(require_role("admin")),
):
    """Invalidate cache entries matching pattern."""

    invalidate_cache(pattern)
    return {"status": "invalidated", "pattern": pattern}


# --- DRIE Endpoints ---

@router.get("/drie/analyze/{habitation_name}", tags=["DRIE"])
def drie_analyze(habitation_name: str):
    """Full DRIE analysis for a single habitation.

    Runs the complete Dynamic Relocation Intelligence Engine pipeline:
    hazard → vulnerability → risk → household breakdown → matching → routes → explainability.
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
    return drie_engine.analyze(hab, sites)


@router.get("/drie/analyze-all", tags=["DRIE"])
def drie_analyze_all():
    """Full DRIE analysis for all habitations with summary."""
    data = load_data()
    sites = data["relocation_sites"]
    return drie_engine.analyze_batch(data["habitations"], sites)


@router.get("/drie/household/{habitation_name}", tags=["DRIE"])
def drie_household(habitation_name: str):
    """Get household-level vulnerability breakdown for a habitation."""
    data = load_data()
    for h in data["habitations"]:
        if h["name"].lower() == habitation_name.lower():
            return household_vulnerability_engine.estimate_breakdown(
                h["population"], h.get("vulnerability", {})
            )
    raise HTTPException(404, f"Habitation '{habitation_name}' not found")


@router.get("/drie/match/{habitation_name}", tags=["DRIE"])
def drie_match(habitation_name: str):
    """Population-to-site matching with real carrying capacity."""
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
    return matching_engine.allocate(hab, ranked)


@router.get("/drie/routes/{habitation_name}", tags=["DRIE"])
def drie_routes(habitation_name: str):
    """Route intelligence with primary/backup routes and safety analysis."""
    data = load_data()
    hab = None
    for h in data["habitations"]:
        if h["name"].lower() == habitation_name.lower():
            hab = h
            break
    if not hab:
        raise HTTPException(404, f"Habitation '{habitation_name}' not found")

    sites = [s for s in data["relocation_sites"] if s["habitation"] == hab["name"]]
    if not sites:
        raise HTTPException(404, "No relocation sites found for this habitation")

    primary = max(sites, key=lambda s: s.get("suitability_score", 0))
    return route_intelligence_engine.analyze_routes(
        {"lat": hab["lat"], "lon": hab["lon"]},
        {"lat": primary["lat"], "lon": primary["lon"]},
    )


@router.post("/drie/simulate", tags=["DRIE"])
def drie_simulate(params: ScenarioRequest):
    """Multi-hazard disaster simulation across all habitations."""
    data = load_data()
    sim_params = {
        "rainfall_delta": params.rainfall_delta,
        "seismic_magnitude": params.seismic_magnitude,
        "landslide_trigger": params.landslide_trigger,
        "river_level_rise": params.river_level_rise,
        "embankment_breach": params.embankment_breach,
        "population_growth_pct": params.population_growth_pct,
    }
    return multi_hazard_simulator.simulate_batch(data["habitations"], sim_params)


@router.get("/drie/presets", tags=["DRIE"])
def drie_presets():
    """Get predefined simulation presets."""
    return multi_hazard_simulator.get_presets()


@router.post("/drie/report", tags=["DRIE"])
def drie_report(event_data: dict):
    """Generate emergency situation report (SitRep)."""
    return report_generator.generate_sitrep(event_data)


@router.get("/drie/report/sitrep", tags=["DRIE"])
def drie_sitrep():
    """Generate SitRep for current at-risk habitations."""
    data = load_data()
    habitations = data["habitations"]
    immediate = [h for h in habitations if h["risk"]["band"] == "immediate"]
    short_term = [h for h in habitations if h["risk"]["band"] == "short_term"]

    event_data = {
        "timestamp": "2026-09-15T10:00:00",
        "affected_habitations": [
            {
                "name": h["name"],
                "population": h["population"],
                "band": h["risk"]["band"],
                "risk_score": h["risk"]["overall"],
                "vulnerability": h.get("vulnerability", {}),
            }
            for h in immediate + short_term
        ],
    }
    return report_generator.generate_sitrep(event_data)


@router.post("/drie/relocation-plan", tags=["DRIE"])
def drie_relocation_plan(habitation_name: str):
    """Generate relocation action plan for a habitation."""
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
    allocation = matching_engine.allocate(hab, ranked)
    return report_generator.generate_relocation_plan(allocation)


# --- Workflow Endpoints ---

@router.get("/workflow/list", tags=["Workflow"])
def workflow_list(state: Optional[str] = None, item_type: Optional[str] = None):
    """List workflow items with optional filters."""
    return workflow_manager.list_items(state=state, item_type=item_type)


@router.get("/workflow/{item_id}", tags=["Workflow"])
def workflow_get(item_id: str):
    """Get a specific workflow item."""
    item = workflow_manager.get(item_id)
    if not item:
        raise HTTPException(404, f"Workflow item '{item_id}' not found")
    return item


@router.post("/workflow/create", tags=["Workflow"])
def workflow_create(item_type: str, habitation: str, data: dict = {}):
    """Create a new workflow item."""
    return workflow_manager.create(item_type, habitation, data)


@router.post("/workflow/transition", tags=["Workflow"])
def workflow_transition(req: WorkflowTransitionRequest):
    """Transition a workflow item to a new state."""
    result = workflow_manager.transition(req.item_id, req.new_state, req.actor, req.note)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result


@router.get("/workflow/stats", tags=["Workflow"])
def workflow_stats():
    """Get workflow statistics."""
    return workflow_manager.stats()


# --- Real Rainfall Data Endpoints ---

RAINFALL_DATA = None
RAINFALL_PATH = Path(__file__).parent.parent.parent / "data" / "assam" / "rainfall_real.json"


def load_rainfall():
    global RAINFALL_DATA
    if RAINFALL_DATA is None:
        if not RAINFALL_PATH.exists():
            raise HTTPException(500, "Rainfall data not ingested. Run rainfall_ingestion.py first.")
        RAINFALL_DATA = json.loads(RAINFALL_PATH.read_text())
    return RAINFALL_DATA


@router.get("/rainfall/summary", tags=["Rainfall"])
def rainfall_summary():
    """Assam-wide rainfall summary with per-district totals."""
    data = load_rainfall()
    tel = data.get("telemetry_hourly_rainfall", {})
    districts = []
    for dist, d in tel.items():
        districts.append({
            "district": dist,
            "total_mm": d["total_mm"],
            "station_count": d["station_count"],
            "max_hourly_mm": d["max_hourly_mm"],
            "annual_rainfall_mm": d["annual_rainfall_mm"],
            "lat": d["lat"],
            "lon": d["lon"],
        })
    districts.sort(key=lambda x: x["total_mm"], reverse=True)
    return {
        "state": "Assam",
        "total_districts": len(districts),
        "total_records": sum(d["n_records"] for d in tel.values()),
        "districts": districts,
    }


@router.get("/rainfall/district/{name}", tags=["Rainfall"])
def rainfall_district(name: str):
    """Detailed rainfall data for a specific district."""
    data = load_rainfall()
    tel = data.get("telemetry_hourly_rainfall", {})
    manual = data.get("manual_daily_rainfall", {})
    rwl = data.get("river_water_level", {})

    # Match district (case-insensitive)
    result = None
    for dist, d in tel.items():
        if dist.lower() == name.lower():
            result = d.copy()
            break

    if not result:
        # Try manual data
        for dist, d in manual.items():
            if dist.lower() == name.lower():
                result = {
                    "district": dist,
                    "station_count": d["station_count"],
                    "stations": d["stations"],
                    "total_mm": d["total_mm"],
                    "max_daily_mm": d["max_daily_mm"],
                    "n_records": d["n_records"],
                    "monthly_rainfall_mm": d["monthly_rainfall_mm"],
                    "source": "manual_daily",
                }
                break

    if not result:
        raise HTTPException(404, f"District '{name}' not found in rainfall data")

    # Attach river data if available
    for dist, d in rwl.items():
        if dist.lower() == name.lower():
            result["river_water_level"] = d
            break

    return result


@router.get("/rainfall/timeseries/{name}", tags=["Rainfall"])
def rainfall_timeseries(name: str, source: str = "tel"):
    """Monthly rainfall timeseries for charting.

    source: 'tel' for telemetry hourly, 'manual' for manual daily.
    """
    data = load_rainfall()
    if source == "manual":
        src = data.get("manual_daily_rainfall", {})
    else:
        src = data.get("telemetry_hourly_rainfall", {})

    for dist, d in src.items():
        if dist.lower() == name.lower():
            monthly = d.get("monthly_rainfall_mm", {})
            return {
                "district": dist,
                "source": source,
                "timeseries": [{"month": k, "rainfall_mm": v} for k, v in monthly.items()],
            }

    raise HTTPException(404, f"District '{name}' not found")


@router.get("/rainfall/stations", tags=["Rainfall"])
def rainfall_stations():
    """List all rainfall monitoring stations across Assam."""
    data = load_rainfall()
    tel = data.get("telemetry_hourly_rainfall", {})
    stations = []
    for dist, d in tel.items():
        for st in d.get("stations", []):
            stations.append({
                "station": st,
                "district": dist,
                "lat": d["lat"],
                "lon": d["lon"],
            })
    return stations


@router.get("/rainfall/river-levels", tags=["Rainfall"])
def rainfall_river_levels():
    """River water level data for districts with gauges."""
    data = load_rainfall()
    rwl = data.get("river_water_level", {})
    return list(rwl.values())
