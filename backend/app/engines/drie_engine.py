"""DRIE — Dynamic Relocation Intelligence Engine.

Orchestrates all sub-engines into a single relocation decision pipeline.
This is the 'brain' of SafeHabitat AI.
"""
from app.engines.risk_engine import risk_engine
from app.engines.hazard_engine import hazard_engine
from app.engines.vulnerability_engine import vulnerability_engine
from app.engines.relocation_engine import relocation_engine
from app.engines.matching_engine import matching_engine
from app.engines.route_intelligence import route_intelligence_engine
from app.engines.household_vulnerability import household_vulnerability_engine
from app.engines.shap_explainer import explainer as shap_explainer
from app.engines.nlg_engine import nlg_engine


class DRIEEngine:
    """End-to-end relocation decision engine."""

    def analyze(self, habitation: dict, sites: list, hazard_events: list = None) -> dict:
        """Full DRIE analysis for a single habitation."""
        name = habitation.get("name", "Unknown")
        population = habitation.get("population", 0)
        lat = habitation.get("lat", 0)
        lon = habitation.get("lon", 0)

        # Step 1: Hazard assessment
        h_flood = habitation.get("hazard", {}).get("flood", 0.5)
        h_landslide = habitation.get("hazard", {}).get("landslide", 0.3)
        h_erosion = habitation.get("hazard", {}).get("erosion", 0.3)
        h_seismic = habitation.get("hazard", {}).get("seismic", 0.5)
        hazard = hazard_engine.combine_hazard(h_flood, h_landslide, h_seismic, h_erosion)

        # Step 2: Vulnerability assessment
        vuln_features = {
            "poverty_index": habitation.get("vulnerability", {}).get("poverty_index", 0.3),
            "age_vulnerability": habitation.get("vulnerability", {}).get("age_vulnerability", 0.2),
            "disability_index": habitation.get("vulnerability", {}).get("disability_index", 0.1),
            "infra_quality": habitation.get("vulnerability", {}).get("infrastructure_quality", 0.5),
        }
        vuln = vulnerability_engine.predict(vuln_features)

        # Step 3: Household-level vulnerability breakdown
        household = household_vulnerability_engine.estimate_breakdown(
            population, habitation.get("vulnerability", {})
        )

        # Step 4: Risk score (multiplicative)
        # Build full feature set including real IMD rainfall
        rr = habitation.get("real_rainfall", {})
        risk_features = {
            "flood_history": h_flood,
            "landslide_history": h_landslide,
            "poverty_index": vuln_features["poverty_index"],
            "infra_quality": vuln_features["infra_quality"],
            "population": population,
            "seismic_zone": h_seismic,
            "rainfall_annual_mm": rr.get("rainfall_annual_mm", 0),
            "rainfall_max_monthly_mm": rr.get("rainfall_max_monthly_mm", 0),
            "rainfall_monsoon_mm": rr.get("rainfall_monsoon_mm", 0),
            "rainfall_monsoon_pct": rr.get("rainfall_monsoon_pct", 0),
            "river_water_level_max_m": rr.get("river_water_level_max_m", 0),
        }
        risk = risk_engine.compute_risk(
            hazard=hazard.get("combined", 0.4),
            exposure=habitation.get("exposure", 0.5),
            vulnerability=vuln.get("score", 0.3),
            features=risk_features,
        )

        # Step 5: Relocation feasibility & carrying capacity
        relocation = relocation_engine.compute_relocation_feasibility(
            hazard.get("combined", 0.4),
            vuln.get("score", 0.3),
            habitation.get("exposure", 0.5),
            habitation.get("habitation_area_km2", 0.5),
            population,
        )

        # Step 6: Match population to sites
        matching = matching_engine.allocate(habitation, sites)

        # Step 7: Route intelligence for primary allocation
        route = {}
        if matching.get("allocations"):
            primary = matching["allocations"][0]
            route = route_intelligence_engine.analyze_routes(
                {"lat": lat, "lon": lon},
                {"lat": primary.get("site_lat", 0), "lon": primary.get("site_lon", 0)},
            )

        # Step 8: SHAP explainability
        shap_features = {
            **risk_features,  # includes all risk features + rainfall
        }
        shap = shap_explainer.explain_risk(shap_features)

        # Step 9: NLG explanation
        explanation = nlg_engine.explain_risk(
            habitation,
            risk,
            shap,
        )

        return {
            "habitation": name,
            "population": population,
            "coordinates": {"lat": lat, "lon": lon},
            "hazard_assessment": hazard,
            "vulnerability_assessment": vuln,
            "household_breakdown": household,
            "risk_assessment": risk,
            "relocation_feasibility": relocation,
            "site_matching": matching,
            "route_intelligence": route,
            "explainability": shap,
            "nlg_explanation": explanation,
            "confidence": self._compute_confidence(habitation, hazard, vuln, risk),
        }

    def analyze_batch(self, habitations: list, sites: list) -> dict:
        """Analyze all habitations and produce summary."""
        results = [self.analyze(h, sites) for h in habitations]

        immediate = [r for r in results if r["risk_assessment"].get("risk_band") == "immediate"]
        short_term = [r for r in results if r["risk_assessment"].get("risk_band") == "short_term"]
        total_pop = sum(r["population"] for r in results)
        at_risk_pop = sum(r["population"] for r in immediate + short_term)

        return {
            "results": results,
            "summary": {
                "total_habitations": len(results),
                "total_population": total_pop,
                "immediate": len(immediate),
                "short_term": len(short_term),
                "at_risk_population": at_risk_pop,
                "at_risk_pct": round(at_risk_pop / max(total_pop, 1) * 100, 1),
            },
        }

    def _compute_confidence(self, habitation, hazard, vuln, risk) -> dict:
        """Estimate confidence in the analysis based on data quality."""
        data_points = 0
        total = 10

        if habitation.get("population", 0) > 0: data_points += 1
        if habitation.get("hazard", {}).get("flood", 0) > 0: data_points += 1
        if habitation.get("hazard", {}).get("landslide", 0) > 0: data_points += 1
        if habitation.get("vulnerability", {}).get("poverty_index", 0) > 0: data_points += 1
        if habitation.get("vulnerability", {}).get("age_vulnerability", 0) > 0: data_points += 1
        if habitation.get("exposure", 0) > 0: data_points += 1
        if habitation.get("infrastructure", {}).get("connectivity", 0) > 0: data_points += 1
        if habitation.get("habitation_area_km2", 0) > 0: data_points += 1
        if hazard.get("hazard_combined", 0) > 0: data_points += 1
        if vuln.get("vulnerability_combined", 0) > 0: data_points += 1

        score = data_points / total
        label = "high" if score > 0.7 else "medium" if score > 0.4 else "low"

        return {
            "score": round(score, 2),
            "label": label,
            "data_completeness": f"{data_points}/{total}",
            "note": (
                "High confidence: sufficient data for reliable analysis."
                if label == "high"
                else "Moderate confidence: some data gaps may affect accuracy."
                if label == "medium"
                else "Low confidence: significant data gaps. Manual verification recommended."
            ),
        }


drie_engine = DRIEEngine()
