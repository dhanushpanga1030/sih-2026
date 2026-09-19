"""Migrate JSON data to PostGIS database.

Loads assam_data.json into spatial tables.
"""
import json
import os
from pathlib import Path
from sqlalchemy.orm import Session
from app.models.spatial_models import (
    District, Habitation, HazardScore, VulnerabilityScore,
    RiskScore, RelocationSite, Explanation
)
from app.database import Base, engine

IS_SQLITE = "sqlite" in os.getenv("DATABASE_URL", "sqlite:///./safehabitat.db")
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "assam"
BAND_LABELS = {
    "immediate": "Immediate Relocation",
    "short_term": "Short-Term Relocation",
    "medium_term": "Medium-Term Planning",
    "monitor": "Continue Monitoring",
}


def migrate_json_to_db():
    """Main migration function."""
    with open(DATA_DIR / "assam_data.json") as f:
        data = json.load(f)

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        # Build district lookup
        district_map = {}
        for dist in data["districts"]:
            district = District(
                name=dist["name"],
                area_sq_km=dist.get("area_sq_km"),
                population=dist.get("population"),
                division=dist.get("division"),
                geom=f"SRID=4326;POINT({dist['lon']} {dist['lat']})" if (not IS_SQLITE and dist.get("lat") and dist.get("lon")) else None,
            )
            session.add(district)
            session.flush()
            district_map[dist["name"]] = district

        # Habitations are top-level in the JSON
        for hab in data["habitations"]:
            district = district_map.get(hab["district"])
            if not district:
                continue

            lon = hab.get("lon", 89.5 + hash(hab["name"]) % 600 / 100)
            lat = hab.get("lat", 25.5 + hash(hab["name"]) % 300 / 100)

            habitation = Habitation(
                name=hab["name"],
                district_id=district.id,
                population=hab.get("population", 1000),
                area_sq_km=hab.get("area_sq_km", 5),
                elevation_m=hab.get("elevation_m", 50),
                slope_degrees=hab.get("slope_degrees", 2),
                geom=f"SRID=4326;POINT({lon} {lat})" if not IS_SQLITE else None,
                data_source="NRSC/ISRO Flood Hazard Zonation Atlas (1998-2023)",
            )
            session.add(habitation)
            session.flush()

            # Hazard scores (nested under "hazard" key)
            hazard = hab.get("hazard", {})
            # Look up NRSC data from the original district dict
            dist_data = next((d for d in data["districts"] if d["name"] == hab["district"]), {})
            nrsc = dist_data.get("nrsc_flood_data", {})
            session.add(HazardScore(
                habitation_id=habitation.id,
                flood_score=hazard.get("flood"),
                landslide_score=hazard.get("landslide"),
                seismic_score=hazard.get("seismic"),
                erosion_score=hazard.get("erosion"),
                combined_hazard=hazard.get("combined", 0.5),
                nrcs_very_high_villages=nrsc.get("very_high_villages", 0),
                nrcs_high_villages=nrsc.get("high_villages", 0),
                nrcs_moderate_villages=nrsc.get("moderate_villages", 0),
                nrcs_low_villages=nrsc.get("low_villages", 0),
                nrcs_very_low_villages=nrsc.get("very_low_villages", 0),
                nrcs_ranking=nrsc.get("ranking", ""),
                nrcs_hazard_index=nrsc.get("hazard_index", 0),
                nrcs_flood_waves=nrsc.get("flood_waves", 0),
                nrcs_gauge_station=nrsc.get("gauge_station", ""),
                data_source="NRSC/ISRO",
            ))

            # Vulnerability scores (nested under "vulnerability" key)
            vuln = hab.get("vulnerability", {})
            session.add(VulnerabilityScore(
                habitation_id=habitation.id,
                population_density=vuln.get("population_density", 500),
                poverty_index=vuln.get("poverty_index", 0.3),
                age_vulnerability=vuln.get("age_vulnerability", 0.15),
                disability_index=vuln.get("disability_index", 0.02),
                infrastructure_quality=vuln.get("infrastructure_quality", 0.5),
                combined_vulnerability=vuln.get("combined", 0.35),
                weights=vuln.get("weights", {}),
            ))

            # Risk scores (nested under "risk" key)
            risk = hab.get("risk", {})
            session.add(RiskScore(
                habitation_id=habitation.id,
                overall_risk=risk.get("overall", 0.5),
                priority_band=risk.get("band", "monitor"),
                contributing_factors=risk.get("contributing_factors", {}),
                shap_values=risk.get("shap_values", {}),
                data_source="NRSC/ISRO + ML Models",
            ))

        # Relocation sites are top-level
        hab_id_map = {}
        for row in session.query(Habitation).all():
            hab_id_map[row.name] = row.id

        for site in data["relocation_sites"]:
            hab_id = hab_id_map.get(site["habitation"])
            if not hab_id:
                continue

            scores = site.get("scores", {})
            cc = site.get("carrying_capacity", {})
            session.add(RelocationSite(
                habitation_id=hab_id,
                name=site["name"],
                area_sq_km=site.get("area_sq_km", 10),
                existing_population=site.get("existing_population", 5000),
                max_capacity=site.get("max_capacity", 50000),
                water_availability=cc.get("water_availability", 0.7),
                healthcare_access=scores.get("healthcare", 0.6),
                school_access=scores.get("school", 0.5),
                road_access=scores.get("road", 0.6),
                environmental_suitability=scores.get("environment", 0.7),
                suitability_score=site.get("suitability_score", 0.6),
                carrying_capacity_verdict=cc.get("verdict", "feasible"),
                capacity_details=cc,
            ))

        session.commit()
        print(f"Migration complete: {len(district_map)} districts, "
              f"{len(data['habitations'])} habitations, "
              f"{len(data['relocation_sites'])} relocation sites")


if __name__ == "__main__":
    migrate_json_to_db()
