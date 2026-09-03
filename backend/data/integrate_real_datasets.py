"""Integrate real open datasets into SafeHabitat AI training data.

Sources:
- India Flood Inventory v4 (IFI-Impacts): DFSI, flooded area, flood events
- NRSC Flood Hazard Zonation Atlas: district-level hazard data
- Census 2011: population demographics

Merges into assam_data.json for model training.
"""
import csv
import json
from pathlib import Path
from collections import Counter, defaultdict

DATA_DIR = Path(__file__).parent
REAL_DIR = DATA_DIR / "real_datasets"
ASSAM_DIR = DATA_DIR / "assam"


def load_dfsi():
    """Load District Flood Severity Index from IFI-Impacts v4."""
    fp = REAL_DIR / "DFSI.csv"
    data = {}
    with open(fp, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            state = row.get("State_Name", "").strip().upper()
            if state == "ASSAM":
                dist = row[""].strip()
                dfsi = float(row["DFSI"])
                data[dist] = dfsi
    return data


def load_flood_events():
    """Load IFI v3 flood event history for Assam districts."""
    fp = REAL_DIR / "India_Flood_Inventory_v3.csv"
    district_events = defaultdict(list)
    with open(fp, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            state = row.get("State", "").strip().upper()
            if state == "ASSAM":
                dist = row.get("Districts", "").strip()
                if dist:
                    district_events[dist].append({
                        "date": row.get("Start Date", ""),
                        "cause": row.get("Main Cause", ""),
                        "duration_days": row.get("Duration(Days)", ""),
                        "location": row.get("Location", ""),
                        "fatality": row.get("Human fatality", ""),
                        "injured": row.get("Human injured", ""),
                        "displaced": row.get("Human Displaced", ""),
                        "area_affected": row.get("Area Affected", ""),
                    })
    return dict(district_events)


def load_flooded_area():
    """Load district flooded area percentages."""
    fp = REAL_DIR / "District_FloodedArea.csv"
    data = {}
    with open(fp, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            dist = row["Dist_Name"].strip()
            data[dist] = {
                "pct_flooded": float(row.get("Percent_Flooded_Area", 0)),
                "permanent_water": float(row.get("Parmanent_Water", 0)),
                "corrected_pct": float(row.get("Corrected_Percent_Flooded_Area", 0)),
            }
    return data


def normalize_district(name):
    """Normalize district name for fuzzy matching."""
    return name.strip().lower().replace("&", "and").replace("  ", " ")


def match_district(name, candidates):
    """Fuzzy match a district name against candidates."""
    norm = normalize_district(name)
    # Exact match
    for c in candidates:
        if normalize_district(c) == norm:
            return c
    # Partial match
    for c in candidates:
        cn = normalize_district(c)
        if norm in cn or cn in norm:
            return c
    # Word overlap
    words = set(norm.split())
    for c in candidates:
        cw = set(normalize_district(c).split())
        if words & cw and len(words & cw) >= 1:
            return c
    return None


def integrate():
    print("Loading real datasets...")
    dfsi_data = load_dfsi()
    flood_events = load_flood_events()
    flooded_area = load_flooded_area()

    print(f"  DFSI: {len(dfsi_data)} Assam districts")
    print(f"  IFI events: {sum(len(v) for v in flood_events.values())} events across {len(flood_events)} districts")
    print(f"  Flooded area: {len(flooded_area)} districts")

    # Load existing assam data
    fp = ASSAM_DIR / "assam_data.json"
    data = json.loads(fp.read_text())

    # Build candidate lists for matching
    dfsi_candidates = list(dfsi_data.keys())
    area_candidates = list(flooded_area.keys())
    event_candidates = list(flood_events.keys())

    matched_dfsi = 0
    matched_area = 0
    matched_events = 0

    for district in data["districts"]:
        name = district["name"]

        # Match DFSI
        match = match_district(name, dfsi_candidates)
        if match:
            district["dfsi"] = round(dfsi_data[match], 3)
            matched_dfsi += 1

        # Match flooded area
        match = match_district(name, area_candidates)
        if match:
            district["flooded_area_pct"] = round(flooded_area[match]["corrected_pct"], 3)
            district["permanent_water_pct"] = round(flooded_area[match]["permanent_water"], 3)
            matched_area += 1

        # Match flood events
        match = match_district(name, event_candidates)
        if match:
            events = flood_events[match]
            district["historical_flood_events"] = len(events)

            # Compute additional metrics
            durations = [int(e["duration_days"]) for e in events if e["duration_days"].isdigit()]
            fatalities = [int(e["fatality"]) for e in events if e["fatality"].isdigit()]
            displaced = [int(e["displaced"]) for e in events if e["displaced"].isdigit()]

            district["avg_flood_duration_days"] = round(sum(durations) / max(len(durations), 1), 1)
            district["total_flood_fatalities"] = sum(fatalities)
            district["total_flood_displaced"] = sum(displaced)
            district["flood_causes"] = dict(Counter(e["cause"] for e in events if e["cause"]))
            matched_events += 1

        # Update habitations in this district
        for hab in data["habitations"]:
            if hab["district"] == name:
                # Enrich with DFSI if available
                if "dfsi" in district:
                    hab["dfsi"] = district["dfsi"]

                # Enrich with historical flood frequency
                if "historical_flood_events" in district:
                    hab["historical_flood_events"] = district["historical_flood_events"]
                    hab["avg_flood_duration_days"] = district.get("avg_flood_duration_days", 0)
                    hab["total_flood_fatalities"] = district.get("total_flood_fatalities", 0)

                # Enrich with flooded area
                if "flooded_area_pct" in district:
                    hab["corrected_flooded_area_pct"] = district["flooded_area_pct"]

    print(f"\nMatched DFSI: {matched_dfsi}/{len(data['districts'])} districts")
    print(f"Matched flooded area: {matched_area}/{len(data['districts'])} districts")
    print(f"Matched flood events: {matched_events}/{len(data['districts'])} districts")

    # Add metadata
    data["real_dataset_metadata"] = {
        "dfsi": {
            "source": "India Flood Inventory-Impacts v4 (IFI-Impacts), Zenodo 10.5281/zenodo.16994648",
            "description": "District Flood Severity Index from IMD data (1967-2023)",
            "n_districts": matched_dfsi,
        },
        "flood_events": {
            "source": "India Flood Inventory v3, IIT Delhi HydroSense Lab",
            "description": "Historical flood event inventory with district, date, cause, impacts",
            "total_events": sum(len(v) for v in flood_events.values()),
            "n_districts": matched_events,
        },
        "flooded_area": {
            "source": "IFI-Impacts District Flooded Area",
            "description": "District-level percentage of flooded area",
            "n_districts": matched_area,
        },
    }

    # Save
    fp.write_text(json.dumps(data, indent=2))
    print(f"\nSaved enriched data to {fp}")

    # Print sample
    print("\nSample enriched district:")
    for d in data["districts"]:
        if "dfsi" in d and "historical_flood_events" in d:
            print(json.dumps({k: v for k, v in d.items() if k != "lat" and k != "lon"}, indent=2))
            break


if __name__ == "__main__":
    integrate()
