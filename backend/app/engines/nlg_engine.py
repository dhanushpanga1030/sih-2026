"""NLG Engine — Natural Language Generation for risk explanations.

Generates human-readable explanations using templates.
In production, can be swapped with LLM API calls.
"""


class NLGEngine:
    HAZARD_DESCRIPTIONS = {
        "flood_score": "high flood susceptibility",
        "landslide_history": "significant landslide risk from steep terrain",
        "landslide_score": "significant landslide risk from steep terrain",
        "seismic_zone": "located in a high-seismicity zone",
        "seismic_score": "located in a high-seismicity zone",
        "rainfall_mm": "elevated rainfall levels increasing hazard exposure",
        "river_dist_km": "close proximity to river networks",
        "slope": "steep terrain contributing to slope instability",
        "erosion_score": "significant erosion risk",
        "hazard_combined": "high combined hazard exposure",
        "flood_x_vuln": "compounded flood and vulnerability risk",
        "hazard_x_exposure": "high hazard exposure interaction",
        "nrsc_flood_risk": "NRSC-identified flood risk zone",
        "flooded_area_pct": "large historically flooded area",
        "permanent_water": "proximity to permanent water bodies",
    }

    VULN_DESCRIPTIONS = {
        "poverty_index": "high poverty levels reduce community resilience",
        "age_vulnerability": "significant elderly/child population",
        "disability_index": "notable disability prevalence",
        "infra_quality": "limited infrastructure quality",
        "vuln_combined": "high combined vulnerability",
        "pop_density": "high population density",
        "population": "large population at exposure",
    }

    BAND_DESCRIPTIONS = {
        "immediate": "requires immediate relocation planning",
        "short_term": "should be prioritized for short-term relocation",
        "medium_term": "needs monitoring and medium-term preparedness",
        "monitor": "currently at manageable risk levels",
    }

    def explain_risk(self, habitation: dict, risk_data: dict, shap_data: dict = None) -> str:
        """Generate full risk explanation."""
        name = habitation.get("name", "this habitation")
        band = risk_data.get("band", "unknown")
        risk_score = risk_data.get("overall", risk_data.get("overall_risk", 0))
        confidence = risk_data.get("confidence", 0)

        lines = [
            f"**{name}** is classified as **{band.upper()}** priority "
            f"with an overall risk score of {risk_score:.0%} "
            f"(confidence: {confidence:.0%}).",
            "",
        ]

        # Top contributing factors
        if shap_data and "top_factors" in shap_data:
            lines.append("**Primary contributing factors:**")
            for factor in shap_data["top_factors"][:3]:
                desc = self.HAZARD_DESCRIPTIONS.get(factor) or self.VULN_DESCRIPTIONS.get(factor)
                if desc:
                    lines.append(f"- {desc}")
        elif risk_data.get("contributing_factors"):
            lines.append("**Primary contributing factors:**")
            sorted_factors = sorted(
                risk_data["contributing_factors"].items(),
                key=lambda x: x[1], reverse=True
            )
            for factor, value in sorted_factors[:3]:
                desc = self.HAZARD_DESCRIPTIONS.get(factor) or self.VULN_DESCRIPTIONS.get(factor)
                if desc:
                    lines.append(f"- {desc} (contribution: {value:.1%})")

        lines.append("")
        lines.append(f"**Recommended action:** {self.BAND_DESCRIPTIONS.get(band, 'assess further')}.")
        lines.append("")
        lines.append(
            "This is an AI-generated recommendation. Final relocation decisions rest with authorized officials."
        )

        return "\n".join(lines)

    def explain_site_selection(self, site: dict, habitation: dict) -> str:
        """Explain why a relocation site was recommended."""
        name = site.get("name", "this site")
        score = site.get("suitability_score", 0)
        cap = site.get("carrying_capacity", {})
        breakdown = site.get("score_breakdown", {})

        lines = [
            f"**{name}** is the top-ranked relocation site with a suitability score of {score:.0%}.",
            "",
        ]

        # Strengths
        strengths = []
        if breakdown.get("safety", 0) > 0.7:
            strengths.append("high safety rating")
        if breakdown.get("capacity", 0) > 0.7:
            strengths.append("sufficient carrying capacity")
        if breakdown.get("accessibility", 0) > 0.7:
            strengths.append("good road and facility access")
        if breakdown.get("services", 0) > 0.7:
            strengths.append("adequate healthcare and education services")

        if strengths:
            lines.append("**Key strengths:**")
            for s in strengths:
                lines.append(f"- {s}")

        # Capacity verdict
        verdict = cap.get("verdict", "unknown")
        incoming = cap.get("incoming_population", 0)
        available = cap.get("available_capacity", 0)

        lines.append("")
        if verdict == "sufficient":
            lines.append(f"✅ **Carrying capacity:** Site can accommodate {incoming:,} incoming residents "
                        f"(available capacity: {available:,}).")
        else:
            lines.append(f"❌ **Carrying capacity:** Site cannot fully accommodate {incoming:,} incoming residents "
                        f"(available capacity: {available:,}). Additional sites may be needed.")

        lines.append("")
        lines.append(
            "This is an AI-generated recommendation. Final relocation decisions rest with authorized officials."
        )

        return "\n".join(lines)


nlg_engine = NLGEngine()
