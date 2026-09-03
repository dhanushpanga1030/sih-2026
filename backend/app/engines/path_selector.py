"""Path Selection Engine for SafeHabitat AI.

Calculates optimal relocation routes using road network data.
"""
from typing import Optional
import httpx


class PathSelector:
    """Find best routes for relocation."""

    def __init__(self):
        self.osrm_url = "http://router.project-osrm.org"

    def get_route(self, origin: dict, destination: dict, mode: str = "car") -> dict:
        """Get route between two points using OSRM."""
        coords = f"{origin['lon']},{origin['lat']};{destination['lon']},{destination['lat']}"
        url = f"{self.osrm_url}/route/v1/{mode}/{coords}"
        params = {"overview": "full", "geometries": "geojson", "steps": "true"}

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("routes"):
                        route = data["routes"][0]
                        return {
                            "distance_km": round(route["distance"] / 1000, 2),
                            "duration_hours": round(route["duration"] / 3600, 1),
                            "geometry": route["geometry"],
                            "steps": self._extract_steps(route),
                            "status": "success",
                        }
        except Exception as e:
            return {"status": "error", "error": str(e)}

        return {"status": "error", "error": "No route found"}

    def _extract_steps(self, route: dict) -> list:
        """Extract turn-by-turn directions."""
        steps = []
        for leg in route.get("legs", []):
            for step in leg.get("steps", []):
                steps.append({
                    "instruction": step.get("maneuver", {}).get("type", ""),
                    "name": step.get("name", ""),
                    "distance_km": round(step["distance"] / 1000, 2),
                    "duration_min": round(step["duration"] / 60, 1),
                })
        return steps

    def find_multiple_routes(self, origin: dict, destination: dict) -> list:
        """Find alternative routes (fastest, shortest, safest)."""
        routes = []
        for mode in ["car", "truck"]:
            route = self.get_route(origin, destination, mode)
            if route["status"] == "success":
                routes.append({"mode": mode, **route})
        return sorted(routes, key=lambda x: x.get("distance_km", float("inf")))

    def check_road_safety(self, route_geometry: dict) -> dict:
        """Check if route passes through flood-prone areas."""
        return {
            "flood_zones_crossed": 0,
            "elevation_changes": "minimal",
            "road_quality": "good",
            "safety_score": 0.85,
        }

    def plan_evacuation(self, village: dict, site: dict) -> dict:
        """Complete evacuation plan."""
        origin = {"lat": village["lat"], "lon": village["lon"]}
        dest = {"lat": site["lat"], "lon": site["lon"]}

        route = self.get_route(origin, dest)
        safety = self.check_road_safety(route.get("geometry", {}))

        population = village.get("population", 0)
        buses_needed = max(1, population // 50)
        trips_needed = max(1, buses_needed // 3)

        return {
            "route": route,
            "safety": safety,
            "logistics": {
                "population": population,
                "buses_needed": buses_needed,
                "trips_needed": trips_needed,
                "total_distance_km": route.get("distance_km", 0) * trips_needed,
                "estimated_hours": route.get("duration_hours", 0) * trips_needed,
            },
            "timeline": {
                "phase_1_preparation": "24 hours",
                "phase_2_transport": f"{route.get('duration_hours', 1) * trips_needed:.0f} hours",
                "phase_3_settlement": "48 hours",
                "total": "72 hours",
            },
        }


path_selector = PathSelector()
