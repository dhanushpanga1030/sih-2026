"""Population-to-Site Matching Engine.

Solves the assignment problem: allocate displaced populations to
relocation sites respecting capacity constraints.

Uses a greedy bin-packing approach (efficient for the problem size).
"""


class MatchingEngine:
    """Match displaced populations to safe relocation sites."""

    def allocate(self, habitation: dict, sites: list) -> dict:
        """Allocate habitation population across ranked relocation sites.

        Returns allocation plan with primary/secondary sites, overflow handling.
        """
        population = habitation.get("population", 0)
        if population <= 0:
            return {"allocations": [], "total_allocated": 0, "unallocated": 0}

        # Sort sites by suitability (best first)
        ranked = sorted(sites, key=lambda s: s.get("suitability_score", 0), reverse=True)

        allocations = []
        remaining = population

        for site in ranked:
            if remaining <= 0:
                break

            cap = site.get("carrying_capacity", {})
            available = cap.get("available_capacity", 0)

            if available <= 0:
                continue

            allocated = min(remaining, available)
            remaining -= allocated

            route_type = "primary" if len(allocations) == 0 else "secondary" if len(allocations) < 3 else "overflow"

            allocations.append({
                "site_name": site.get("name", "Unknown"),
                "site_lat": site.get("lat", 0),
                "site_lon": site.get("lon", 0),
                "allocated_population": allocated,
                "site_capacity": site.get("max_capacity", 0),
                "available_capacity": available,
                "capacity_utilization": round(allocated / max(available, 1) * 100, 1),
                "suitability_score": site.get("suitability_score", 0),
                "route_type": route_type,
                "carrying_capacity": cap,
            })

        total_allocated = population - remaining
        coverage = round(total_allocated / max(population, 1) * 100, 1)

        return {
            "habitation": habitation.get("name", "Unknown"),
            "population": population,
            "allocations": allocations,
            "total_allocated": total_allocated,
            "unallocated": remaining,
            "coverage_pct": coverage,
            "sites_used": len(allocations),
            "recommendation": self._generate_recommendation(allocations, remaining, population),
        }

    def reallocate(self, habitation: dict, sites: list, blocked_site: str = None) -> dict:
        """Reallocate when a site becomes unavailable (flood, road block, etc.)."""
        filtered = [s for s in sites if s.get("name", "").lower() != blocked_site.lower()] if blocked_site else sites
        result = self.allocate(habitation, filtered)
        result["reallocation_reason"] = f"Site '{blocked_site}' unavailable" if blocked_site else None
        return result

    def calculate_logistics(self, allocation: dict, village_lat: float, village_lon: float) -> dict:
        """Calculate transport logistics for a single allocation."""
        pop = allocation.get("allocated_population", 0)
        distance = self._haversine_km(
            village_lat, village_lon,
            allocation.get("site_lat", 0), allocation.get("site_lon", 0)
        )

        buses = max(1, (pop + 49) // 50)
        trips = max(1, (buses + 2) // 3)
        hours_per_trip = max(0.5, distance / 30)  # ~30 km/h average
        total_hours = round(hours_per_trip * trips, 1)

        return {
            "distance_km": round(distance, 2),
            "buses_needed": buses,
            "trips_needed": trips,
            "hours_per_trip": round(hours_per_trip, 1),
            "total_transport_hours": total_hours,
            "personnel_needed": buses * 2 + 5,  # 2 crew per bus + 5 coordinators
        }

    def _haversine_km(self, lat1, lon1, lat2, lon2) -> float:
        import math
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        return R * 2 * math.asin(math.sqrt(a))

    def _generate_recommendation(self, allocations: list, unallocated: int, population: int) -> str:
        if unallocated == 0:
            return f"All {population:,} residents can be accommodated across {len(allocations)} sites."
        coverage = round((population - unallocated) / max(population, 1) * 100, 1)
        return (
            f"Only {coverage}% coverage ({population - unallocated:,}/{population:,}). "
            f"{unallocated:,} residents need additional relocation sites or temporary shelters."
        )


matching_engine = MatchingEngine()
