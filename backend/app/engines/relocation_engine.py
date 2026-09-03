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
            capacity = min(site.get("max_capacity", 1000) / max(habitation.get("population", 1), 1), 1.0)
            accessibility = (scores.get("road", 0.5) + scores.get("healthcare", 0.5) + scores.get("school", 0.5)) / 3
            services = (scores.get("healthcare", 0.5) + scores.get("school", 0.5)) / 2
            environment = scores.get("environment", 0.5)
            livelihood = scores.get("livelihood", 0.5)

            suitability = (
                weights["safety"] * safety +
                weights["capacity"] * capacity +
                weights["accessibility"] * accessibility +
                weights["services"] * services +
                weights["environment"] * environment +
                weights["livelihood"] * livelihood
            )

            capacity_check = self.check_carrying_capacity(habitation, site)

            ranked.append({
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
            })

        return sorted(ranked, key=lambda x: x["suitability_score"], reverse=True)

    def check_carrying_capacity(self, habitation: dict, site: dict) -> dict:
        """Check if site can sustainably support incoming population."""
        incoming = habitation.get("population", 0)
        max_cap = site.get("max_capacity", 0)
        existing = site.get("existing_population", 0)
        available = max_cap - existing

        water = site.get("carrying_capacity", {}).get("water_availability", 0.5)
        scores = site.get("scores", {})
        health = scores.get("healthcare", 0.5)
        school = scores.get("school", 0.5)
        road = scores.get("road", 0.5)

        infra_rating = round((health + school + road) / 3, 3)

        if available >= incoming and infra_rating >= 0.4 and water >= 0.3:
            verdict = "sufficient"
        else:
            verdict = "insufficient"

        return {
            "verdict": verdict,
            "incoming_population": incoming,
            "site_capacity": max_cap,
            "existing_population": existing,
            "available_capacity": available,
            "capacity_gap": available - incoming,
            "infrastructure_rating": infra_rating,
            "water_availability": water,
        }


relocation_engine = RelocationEngine()
