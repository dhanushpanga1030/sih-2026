"""Multi-Hazard Disaster Simulation Engine.

Simulates compound disaster scenarios beyond simple rainfall delta.
Supports: flood, landslide, seismic, river-level, embankment-breach, compound events.
"""

BAND_THRESHOLDS = {"immediate": 0.65, "short_term": 0.50, "medium_term": 0.35}


class MultiHazardSimulator:
    """Run multi-parameter disaster simulations."""

    def simulate(self, habitation: dict, params: dict) -> dict:
        """Run simulation with multiple hazard parameters."""
        h = habitation.get("hazard", {})
        v = habitation.get("vulnerability", {})
        exposure = habitation.get("exposure", 0.5)

        # Original values
        orig_flood = h.get("flood", 0.5)
        orig_landslide = h.get("landslide", 0.3)
        orig_seismic = h.get("seismic", 0.5)
        orig_erosion = h.get("erosion", 0.3)
        orig_combined = h.get("combined", 0.4)

        # Apply deltas
        flood_delta = params.get("rainfall_delta", 0) / 100
        seismic_magnitude = params.get("seismic_magnitude", 0)
        landslide_trigger = params.get("landslide_trigger", 0) / 100
        river_level_rise = params.get("river_level_rise", 0) / 100
        embankment_breach = params.get("embankment_breach", False)
        population_growth = params.get("population_growth_pct", 0) / 100

        new_flood = min(1.0, orig_flood * (1 + flood_delta + river_level_rise + (0.3 if embankment_breach else 0)))
        new_landslide = min(1.0, orig_landslide * (1 + landslide_trigger + flood_delta * 0.5))
        new_seismic = min(1.0, orig_seismic * (1 + seismic_magnitude * 0.15))
        new_erosion = min(1.0, orig_erosion * (1 + flood_delta * 0.3))

        new_combined = round(
            0.35 * new_flood + 0.25 * new_landslide + 0.25 * new_seismic + 0.15 * new_erosion, 3
        )

        # Adjust exposure for population growth
        new_exposure = min(1.0, exposure * (1 + population_growth))

        # Risk calculation (multiplicative)
        new_risk = round(
            (new_combined ** 0.4) * (new_exposure ** 0.3) * (v.get("combined", 0.5) ** 0.3), 3
        )
        new_risk = min(1.0, new_risk)

        # Band classification
        old_risk = habitation.get("risk", {}).get("overall", 0.5)
        old_band = habitation.get("risk", {}).get("band", "medium_term")
        new_band = self._classify(new_risk)

        return {
            "habitation": habitation.get("name", "Unknown"),
            "original": {
                "flood": orig_flood, "landslide": orig_landslide,
                "seismic": orig_seismic, "erosion": orig_erosion,
                "hazard_combined": orig_combined, "risk": old_risk, "band": old_band,
            },
            "simulated": {
                "flood": round(new_flood, 3), "landslide": round(new_landslide, 3),
                "seismic": round(new_seismic, 3), "erosion": round(new_erosion, 3),
                "hazard_combined": new_combined, "risk": new_risk, "band": new_band,
            },
            "parameters": params,
            "risk_change": round(new_risk - old_risk, 4),
            "band_changed": old_band != new_band,
            "severity_delta": self._severity_label(old_band, new_band),
        }

    def simulate_batch(self, habitations: list, params: dict) -> dict:
        results = [self.simulate(h, params) for h in habitations]
        results.sort(key=lambda x: x["risk_change"], reverse=True)

        band_changes = [r for r in results if r["band_changed"]]
        newly_immediate = [r for r in results if r["simulated"]["band"] == "immediate" and r["original"]["band"] != "immediate"]

        return {
            "scenario": params,
            "total_habitations": len(results),
            "results": results,
            "summary": {
                "band_changes": len(band_changes),
                "newly_immediate": len(newly_immediate),
                "max_risk_change": results[0]["risk_change"] if results else 0,
                "affected_habitations": [r["habitation"] for r in newly_immediate],
            },
        }

    def get_presets(self) -> list:
        return [
            {"name": "Normal Monsoon", "rainfall_delta": 0, "seismic_magnitude": 0, "landslide_trigger": 0},
            {"name": "Heavy Rainfall (+30%)", "rainfall_delta": 30, "seismic_magnitude": 0, "landslide_trigger": 10},
            {"name": "Extreme Flood (+60%)", "rainfall_delta": 60, "seismic_magnitude": 0, "landslide_trigger": 20, "river_level_rise": 40},
            {"name": "Earthquake (5.5 Richter)", "rainfall_delta": 0, "seismic_magnitude": 5.5, "landslide_trigger": 30},
            {"name": "Compound: Flood + Landslide", "rainfall_delta": 40, "seismic_magnitude": 0, "landslide_trigger": 40, "river_level_rise": 20},
            {"name": "Worst Case", "rainfall_delta": 80, "seismic_magnitude": 4.0, "landslide_trigger": 50, "river_level_rise": 60, "embankment_breach": True},
        ]

    def _classify(self, risk: float) -> str:
        if risk >= 0.65: return "immediate"
        if risk >= 0.50: return "short_term"
        if risk >= 0.35: return "medium_term"
        return "monitor"

    def _severity_label(self, old_band: str, new_band: str) -> str:
        order = {"monitor": 0, "medium_term": 1, "short_term": 2, "immediate": 3}
        diff = order.get(new_band, 0) - order.get(old_band, 0)
        if diff > 0: return f"escalated_{diff}_level(s)"
        if diff < 0: return f"de-escalated_{abs(diff)}_level(s)"
        return "unchanged"


multi_hazard_simulator = MultiHazardSimulator()
