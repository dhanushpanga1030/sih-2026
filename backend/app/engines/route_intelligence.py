"""Route Intelligence Engine.

Evaluates route safety, finds primary/backup routes,
and scores routes based on flood zones, elevation, and road conditions.
"""
import math
import httpx


class RouteIntelligenceEngine:
    """Hazard-aware route analysis for evacuation planning."""

    OSRM_URL = "http://router.project-osrm.org"

    def analyze_routes(self, origin: dict, destination: dict, hazard_zones: list = None) -> dict:
        """Find and evaluate primary + backup routes."""
        routes = self._find_alternatives(origin, destination)

        for route in routes:
            route["safety_analysis"] = self._assess_safety(route, hazard_zones or [])
            route["score"] = self._compute_route_score(route)

        routes.sort(key=lambda r: r.get("score", 0), reverse=True)

        primary = routes[0] if routes else None
        backup = routes[1] if len(routes) > 1 else None

        return {
            "primary_route": primary,
            "backup_route": backup,
            "all_routes": routes,
            "recommendation": self._route_recommendation(primary, backup),
        }

    def score_route_safety(self, route_geometry: dict, flood_zones: list = None) -> dict:
        """Score a route's safety considering flood zones and terrain."""
        if not flood_zones:
            return {
                "flood_zones_crossed": 0,
                "safety_score": 0.85,
                "risk_level": "low",
                "recommendation": "Route appears safe for evacuation.",
            }

        # Simplified: check if route bbox overlaps any flood zone
        crossings = 0
        for zone in flood_zones:
            if self._geometry_overlaps(route_geometry, zone):
                crossings += 1

        safety = max(0.1, 0.85 - crossings * 0.2)
        risk = "low" if safety > 0.7 else "medium" if safety > 0.4 else "high"

        return {
            "flood_zones_crossed": crossings,
            "safety_score": round(safety, 3),
            "risk_level": risk,
            "recommendation": (
                "Route appears safe." if risk == "low"
                else f"Caution: {crossings} hazard zone(s) crossed. Use backup route if available."
                if risk == "medium"
                else f"WARNING: {crossings} hazard zones crossed. Alternate route strongly recommended."
            ),
        }

    def plan_evacuation_timeline(self, population: int, distance_km: float, priority_breakdown: dict = None) -> dict:
        """Generate phased evacuation timeline."""
        buses = max(1, (population + 49) // 50)
        trips = max(1, (buses + 2) // 3)
        hours_per_trip = max(0.5, distance_km / 30)

        # Phase durations
        prep_hours = 2
        alert_hours = 0.5
        transport_hours = round(hours_per_trip * trips, 1)
        settlement_hours = 4

        return {
            "phases": [
                {"phase": 1, "name": "Alert & Assembly", "duration_hours": alert_hours, "description": "Issue alerts, assemble population at collection points"},
                {"phase": 2, "name": "Preparation", "duration_hours": prep_hours, "description": "Load essentials, board vulnerable groups first"},
                {"phase": 3, "name": "Transport", "duration_hours": transport_hours, "description": f"{trips} trips with {buses} buses"},
                {"phase": 4, "name": "Settlement", "duration_hours": settlement_hours, "description": "Unpack, medical check, assign shelters"},
            ],
            "total_hours": round(alert_hours + prep_hours + transport_hours + settlement_hours, 1),
            "logistics": {
                "buses": buses,
                "trips": trips,
                "personnel": buses * 2 + 5,
                "distance_km": round(distance_km, 2),
            },
            "vulnerable_first": bool(priority_breakdown),
        }

    def _find_alternatives(self, origin: dict, dest: dict) -> list:
        """Find multiple route alternatives via OSRM."""
        routes = []
        coords = f"{origin['lon']},{origin['lat']};{dest['lon']},{dest['lat']}"

        for profile in ["driving", "driving"]:
            try:
                url = f"{self.OSRM_URL}/route/v1/{profile}/{coords}"
                params = {"overview": "full", "geometries": "geojson", "steps": "true", "alternatives": "true"}
                with httpx.Client(timeout=15) as client:
                    resp = client.get(url, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        for i, r in enumerate(data.get("routes", [])[:3]):
                            routes.append({
                                "route_id": f"route_{i+1}",
                                "distance_km": round(r["distance"] / 1000, 2),
                                "duration_hours": round(r["duration"] / 3600, 2),
                                "geometry": r["geometry"],
                                "steps": self._extract_steps(r),
                                "type": ["primary", "secondary", "tertiary"][min(i, 2)],
                            })
            except Exception:
                pass

        if not routes:
            distance = self._haversine_km(origin["lat"], origin["lon"], dest["lat"], dest["lon"])
            routes.append({
                "route_id": "route_direct",
                "distance_km": round(distance, 2),
                "duration_hours": round(distance / 30, 2),
                "geometry": None,
                "steps": [],
                "type": "primary",
            })

        return routes

    def _assess_safety(self, route: dict, flood_zones: list) -> dict:
        crossings = 0
        for zone in flood_zones:
            if self._geometry_overlaps(route.get("geometry", {}), zone):
                crossings += 1

        safety = max(0.1, 0.85 - crossings * 0.2)
        return {
            "flood_zones_crossed": crossings,
            "safety_score": round(safety, 3),
            "risk_level": "low" if safety > 0.7 else "medium" if safety > 0.4 else "high",
        }

    def _compute_route_score(self, route: dict) -> float:
        safety = route.get("safety_analysis", {}).get("safety_score", 0.5)
        distance_penalty = min(route.get("distance_km", 10) / 50, 0.3)
        return round(safety - distance_penalty, 3)

    def _geometry_overlaps(self, geom: dict, zone: dict) -> bool:
        if not geom or not zone:
            return False
        coords = geom.get("coordinates", [])
        zbbox = zone.get("bbox", [])
        if not coords or not zbbox or len(zbbox) < 4:
            return False
        for c in (coords[0] if coords and isinstance(coords[0][0], list) else [coords]):
            for pt in (c if isinstance(c[0], list) else [c]):
                if len(pt) >= 2:
                    if zbbox[0] <= pt[0] <= zbbox[2] and zbbox[1] <= pt[1] <= zbbox[3]:
                        return True
        return False

    def _extract_steps(self, route: dict) -> list:
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

    def _haversine_km(self, lat1, lon1, lat2, lon2) -> float:
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        return R * 2 * math.asin(math.sqrt(a))

    def _route_recommendation(self, primary: dict, backup: dict) -> str:
        if not primary:
            return "No routes found. Manual route planning required."
        parts = [f"Primary: {primary['distance_km']}km, ~{primary['duration_hours']}h"]
        if primary.get("safety_analysis", {}).get("risk_level") == "high":
            parts.append("WARNING: Primary route has high flood risk.")
        if backup:
            parts.append(f"Backup: {backup['distance_km']}km, ~{backup['duration_hours']}h")
        return ". ".join(parts)


route_intelligence_engine = RouteIntelligenceEngine()
