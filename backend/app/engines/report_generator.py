"""Emergency Situation Report (SitRep) Generator.

Generates structured government reports for disaster events.
"""


class ReportGenerator:
    """Generate emergency situation reports and decision-support documents."""

    def generate_sitrep(self, event_data: dict) -> dict:
        """Generate a complete Situation Report."""
        habitations = event_data.get("affected_habitations", [])
        timestamp = event_data.get("timestamp", "2026-01-01T00:00:00")

        total_pop = sum(h.get("population", 0) for h in habitations)
        immediate = [h for h in habitations if h.get("band") == "immediate"]
        short_term = [h for h in habitations if h.get("band") == "short_term"]

        # Vulnerable population
        total_children = sum(h.get("vulnerability", {}).get("breakdown", {}).get("children", 0) for h in habitations)
        total_elderly = sum(h.get("vulnerability", {}).get("breakdown", {}).get("elderly", 0) for h in habitations)
        total_disabled = sum(h.get("vulnerability", {}).get("breakdown", {}).get("persons_with_disability", 0) for h in habitations)

        sections = [
            self._header(timestamp),
            self._executive_summary(total_pop, len(immediate), len(habitations)),
            self._affected_areas(habitations),
            self._vulnerable_population(total_children, total_elderly, total_disabled, total_pop),
            self._relocation_needs(immediate, short_term),
            self._recommendations(immediate, short_term),
            self._disclaimer(),
        ]

        return {
            "report_type": "Situation Report (SitRep)",
            "timestamp": timestamp,
            "severity": self._severity_level(immediate, habitations),
            "sections": sections,
            "metadata": {
                "total_habitations": len(habitations),
                "total_population": total_pop,
                "immediate_count": len(immediate),
                "short_term_count": len(short_term),
            },
            "text": "\n\n".join(sections),
        }

    def generate_relocation_plan(self, allocation_data: dict) -> dict:
        """Generate a relocation action plan."""
        hab = allocation_data.get("habitation", "Unknown")
        pop = allocation_data.get("population", 0)
        allocations = allocation_data.get("allocations", [])

        lines = [
            f"RELOCATION ACTION PLAN — {hab}",
            f"Population to relocate: {pop:,}",
            "",
            "SITE ALLOCATIONS:",
        ]

        for i, a in enumerate(allocations, 1):
            lines.append(
                f"  {i}. {a['site_name']} — {a['allocated_population']:,} people "
                f"({a['capacity_utilization']}% capacity utilized)"
            )

        unallocated = allocation_data.get("unallocated", 0)
        if unallocated > 0:
            lines.append(f"\n  ⚠ {unallocated:,} residents require additional sites.")

        lines.extend([
            "",
            f"Total sites used: {len(allocations)}",
            f"Coverage: {allocation_data.get('coverage_pct', 0)}%",
            "",
            "DISCLAIMER: AI-generated plan. Final decisions rest with authorized officials.",
        ])

        return {
            "plan_type": "Relocation Action Plan",
            "habitation": hab,
            "text": "\n".join(lines),
            "allocations": allocations,
            "coverage_pct": allocation_data.get("coverage_pct", 0),
        }

    def _header(self, timestamp: str) -> str:
        return (
            "=" * 60 + "\n"
            "EMERGENCY SITUATION REPORT (SitRep)\n"
            "SafeHabitat AI — Disaster Risk & Relocation Decision Platform\n"
            f"Generated: {timestamp}\n"
            "=" * 60
        )

    def _executive_summary(self, total_pop: int, immediate_count: int, total: int) -> str:
        return (
            "EXECUTIVE SUMMARY\n\n"
            f"The platform has identified {total} affected habitations with a combined "
            f"population of {total_pop:,}. Of these, {immediate_count} habitations are "
            f"classified as IMMEDIATE priority requiring urgent relocation planning."
        )

    def _affected_areas(self, habitations: list) -> str:
        lines = ["AFFECTED AREAS\n"]
        for h in sorted(habitations, key=lambda x: x.get("risk_score", 0), reverse=True)[:10]:
            name = h.get("name", "Unknown")
            pop = h.get("population", 0)
            risk = h.get("risk_score", 0)
            band = h.get("band", "unknown")
            lines.append(f"  • {name} — Pop: {pop:,} | Risk: {risk:.0%} | Band: {band.upper()}")
        if len(habitations) > 10:
            lines.append(f"  ... and {len(habitations) - 10} more")
        return "\n".join(lines)

    def _vulnerable_population(self, children: int, elderly: int, disabled: int, total: int) -> str:
        return (
            "VULNERABLE POPULATION\n\n"
            f"  Children (0-14):      {children:,} ({children/max(total,1)*100:.1f}%)\n"
            f"  Elderly (65+):        {elderly:,} ({elderly/max(total,1)*100:.1f}%)\n"
            f"  Persons with disability: {disabled:,} ({disabled/max(total,1)*100:.1f}%)\n\n"
            "  Priority 1 (Assisted evacuation): Disabled, medically dependent, pregnant\n"
            "  Priority 2 (Priority transport): Children and elderly\n"
            "  Priority 3 (Support needed): Female-headed households\n"
            "  Priority 4 (Standard): General population"
        )

    def _relocation_needs(self, immediate: list, short_term: list) -> str:
        lines = ["RELOCATION NEEDS\n"]
        if immediate:
            lines.append(f"  IMMEDIATE ({len(immediate)} habitations):")
            for h in immediate:
                lines.append(f"    - {h.get('name')}: {h.get('population', 0):,} people")
        if short_term:
            lines.append(f"  SHORT-TERM ({len(short_term)} habitations):")
            for h in short_term[:5]:
                lines.append(f"    - {h.get('name')}: {h.get('population', 0):,} people")
        return "\n".join(lines)

    def _recommendations(self, immediate: list, short_term: list) -> str:
        lines = ["RECOMMENDATIONS\n"]
        if immediate:
            lines.append(f"  1. Initiate IMMEDIATE relocation planning for {len(immediate)} habitations")
            lines.append(f"  2. Deploy emergency response teams to highest-risk areas")
            lines.append(f"  3. Activate relief camps and temporary shelters")
        lines.append(f"  {'4' if immediate else '1'}. Begin short-term preparedness for remaining at-risk habitations")
        lines.append(f"  {'5' if immediate else '2'}. Review and update evacuation routes")
        return "\n".join(lines)

    def _disclaimer(self) -> str:
        return (
            "DISCLAIMER\n\n"
            "This report is generated by the SafeHabitat AI Decision Support Platform. "
            "AI-generated assessments should be validated by authorized officials before "
            "issuing evacuation or relocation orders. Final decisions rest with the "
            "District Disaster Management Authority (DDMA) and State Disaster Management "
            "Authority (SDMA)."
        )

    def _severity_level(self, immediate: list, total: list) -> str:
        ratio = len(immediate) / max(len(total), 1)
        if ratio > 0.3: return "critical"
        if ratio > 0.1: return "high"
        if ratio > 0.05: return "moderate"
        return "low"


report_generator = ReportGenerator()
