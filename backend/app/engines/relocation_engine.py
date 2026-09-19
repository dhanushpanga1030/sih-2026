"""Relocation & Carrying Capacity Engine.

Ranks candidate relocation sites and checks carrying capacity.
"""


class RelocationEngine:
    DEFAULT_WEIGHTS = {
        "safety": 0.30,
        "capacity": 0.20,
        "accessibility": 0.15,
        "services": 0.15,
        "environment": 0.10,
        "livelihood": 0.10,
    }

    def rank_sites(self, habitation: dict, sites: list, weights: dict = None) -> list:
        """Rank relocation sites by suitability score."""
        if weights is None:
            weights = self.DEFAULT_WEIGHTS.copy()

        ranked = []
        for site in sites:
            scores = site.get("scores", {})
            safety = scores.get("safety", 0.5)
            capacity = min(
                site.get("max_capacity", 1000) / max(habitation.get("population", 1), 1), 1.0
            )
            accessibility = (
                scores.get("road", 0.5) + scores.get("healthcare", 0.5) + scores.get("school", 0.5)
            ) / 3
            services = (scores.get("healthcare", 0.5) + scores.get("school", 0.5)) / 2
            environment = scores.get("environment", 0.5)
            livelihood = scores.get("livelihood", 0.5)

            suitability = (
                weights["safety"] * safety
                + weights["capacity"] * capacity
                + weights["accessibility"] * accessibility
                + weights["services"] * services
                + weights["environment"] * environment
                + weights["livelihood"] * livelihood
            )

            capacity_check = self.check_carrying_capacity(habitation, site)

            ranked.append(
                {
                    **site,
                    "suitability_score": round(suitability, 3),
                    "score_breakdown": {
                        "safety": round(safety, 3),
                        "capacity": round(capacity, 3),
                        "accessibility": round(accessibility, 3),
                        "services": round(services, 3),
                        "environment": round(environment, 3),
                        "livelihood": round(livelihood, 3),
                    },
                    "carrying_capacity": capacity_check,
                }
            )

        return sorted(ranked, key=lambda x: x["suitability_score"], reverse=True)

    def check_carrying_capacity(self, habitation: dict, site: dict) -> dict:
        """Real carrying capacity: water, sanitation, area, infrastructure."""
        incoming = habitation.get("population", 0)
        max_cap = site.get("max_capacity", 0)
        existing = site.get("existing_population", 0)
        available = max_cap - existing

        cc = site.get("carrying_capacity", {})
        water = cc.get("water_availability", 0.5)
        sanitation = cc.get("sanitation_capacity", 0.5)
        area_km2 = cc.get("area_km2", 1.0)
        healthcare = cc.get("healthcare_beds", 0)

        # Per-person requirements
        water_per_person = water * 200  # liters/day capacity
        sanitation_ratio = sanitation  # fraction that can be served
        area_per_person = area_km2 * 1000 / max(incoming, 1)  # sq meters per person

        # Realistic capacity based on resources
        water_capacity = int(water_per_person * existing / 50) if existing > 0 else int(water_per_person * 1000 / 50)
        sanitation_capacity = int(sanitation_ratio * existing) if existing > 0 else int(sanitation_ratio * 2000)
        area_capacity = int(area_km2 * 250)  # ~250 people per sq km for relief camps
        healthcare_capacity = healthcare * 50 if healthcare > 0 else 500

        real_capacity = min(water_capacity, sanitation_capacity, area_capacity, healthcare_capacity)
        real_available = max(0, real_capacity - existing)

        scores = site.get("scores", {})
        infra_rating = round((scores.get("healthcare", 0.5) + scores.get("school", 0.5) + scores.get("road", 0.5)) / 3, 3)

        if real_available >= incoming and infra_rating >= 0.4 and water >= 0.3:
            verdict = "sufficient"
        elif real_available >= incoming * 0.5:
            verdict = "partial"
        else:
            verdict = "insufficient"

        return {
            "verdict": verdict,
            "incoming_population": incoming,
            "site_capacity": max_cap,
            "real_capacity": real_capacity,
            "existing_population": existing,
            "available_capacity": real_available,
            "capacity_gap": real_available - incoming,
            "infrastructure_rating": infra_rating,
            "water_availability": water,
            "sanitation_capacity": sanitation,
            "area_km2": area_km2,
            "area_per_person_sqm": round(area_per_person, 1),
            "healthcare_beds": healthcare,
            "capacity_breakdown": {
                "water_limited": water_capacity,
                "sanitation_limited": sanitation_capacity,
                "area_limited": area_capacity,
                "healthcare_limited": healthcare_capacity,
            },
        }


    def compute_relocation_feasibility(self, hazard: float, vulnerability: float,
                                        exposure: float, area_km2: float,
                                        population: int) -> dict:
        """Compute relocation feasibility score and recommendation."""
        import math
        risk = (hazard ** 0.4) * (exposure ** 0.3) * (vulnerability ** 0.3)
        risk = min(max(risk, 0), 1)

        pop_density = population / max(area_km2, 0.01)
        threshold = 0.5

        if risk >= 0.65:
            recommendation = "immediate_relocation"
            urgency = "critical"
        elif risk >= 0.50:
            recommendation = "planned_relocation"
            urgency = "high"
        elif risk >= 0.35:
            recommendation = "monitor_and_prepare"
            urgency = "medium"
        else:
            recommendation = "no_action"
            urgency = "low"

        return {
            "feasibility_score": round(1 - risk, 3),
            "risk_score": round(risk, 3),
            "recommendation": recommendation,
            "urgency": urgency,
            "population": population,
            "area_km2": area_km2,
            "pop_density": round(pop_density, 1),
            "needs_relocation": risk >= threshold,
        }


relocation_engine = RelocationEngine()
