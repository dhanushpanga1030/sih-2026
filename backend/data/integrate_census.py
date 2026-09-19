"""Integrate Census 2011 Village Amenities data into assam_data.json.

Aggregates village-level census data to district level and enriches
both districts and habitations with real demographic/infrastructure data.
"""
import json
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent
ASSETS_DIR = Path(r"C:\Users\drpra\OneDrive\Desktop\sih copy\assets")
ASSAM_DIR = DATA_DIR / "assam"

# Status mapping: 1=Available, 2=Not Available
STATUS_MAP = {1: True, 2: False}


def load_census_villages():
    """Load and filter Assam village census data."""
    fp = ASSETS_DIR / "DH_2011_DCHB_Village_Release_1800.xlsx"
    df = pd.read_excel(fp, sheet_name="Village_Data_1800")
    return df[df["State Name"] == "ASSAM"].copy()


def safe_int(series):
    """Convert series to numeric, coerce errors, sum."""
    return int(pd.to_numeric(series, errors="coerce").sum())


def safe_float(series):
    """Convert series to numeric, coerce errors, sum."""
    return float(pd.to_numeric(series, errors="coerce").sum())


def aggregate_district(census_df):
    """Aggregate village data to district level."""
    districts = {}
    for dist_name, group in census_df.groupby("District Name"):
        n = len(group)

        # Population
        total_pop = safe_int(group["Total Population of Village"])
        total_hh = safe_int(group["Total   Households "])
        total_sc = safe_int(group["Total Scheduled Castes Population of Village"])
        total_st = safe_int(group["Total Scheduled Tribes Population of Village"])
        total_male = safe_int(group["Total Male Population of Village"])
        total_female = safe_int(group["Total Female Population of Village"])
        total_area = safe_float(group["Total Geographical Area (in Hectares)"])

        # Education (1=Available, 2=Not Available)
        primary_schools = safe_int(group["Govt Primary School (Numbers)"])
        middle_schools = safe_int(group["Govt  Middle School (Numbers)"])
        secondary_schools = safe_int(group["Govt  Secondary School (Numbers)"])
        sr_sec_schools = safe_int(group["Govt Senior Secondary School (Numbers)"])
        degree_colleges = safe_int(group["Govt  Arts and Science Degree College (Numbers)"])

        # Health
        chc = safe_int(group["Community Health Centre (Numbers)"])
        phc = safe_int(group["Primary Health Centre (Numbers)"])
        sub_centre = safe_int(group["Primary Heallth Sub Centre (Numbers)"])
        maternity = safe_int(group["Maternity And Child Welfare Centre (Numbers)"])
        hospitals = safe_int(group["Hospital Allopathic (Numbers)"])
        dispensaries = safe_int(group["Dispensary (Numbers)"])

        # Water sources (count villages with availability = 1)
        tap_water = int((group["Tap Water-Treated (Status A(1)/NA(2))"] == 1).sum())
        hand_pump = int((group["Hand Pump (Status A(1)/NA(2))"] == 1).sum())
        tube_well = int((group["Tube Wells/Borehole (Status A(1)/NA(2))"] == 1).sum())
        river_canal = int((group["River/Canal (Status A(1)/NA(2))"] == 1).sum())
        tank_pond = int((group["Tank/Pond/Lake (Status A(1)/NA(2))"] == 1).sum())
        spring = int((group["Spring (Status A(1)/NA(2))"] == 1).sum())
        covered_well = int((group["Covered Well (Status A(1)/NA(2))"] == 1).sum())

        # Drainage
        closed_drainage = int((group["Closed Drainage (Status A(1)/NA(2))"] == 1).sum())
        open_drainage = int((group[" Open Drainage (Status A(1)/NA(2))"] == 1).sum())
        no_drainage = int((group["No  Drainage (Status A(1)/NA(2))"] == 1).sum())

        # Sanitation (strip column names to handle leading spaces)
        cols_stripped = {c.strip(): c for c in group.columns}
        tsc_col = cols_stripped.get("Is the Area Covered under Total Sanitation Campaign (TSC)? (Status A(1)/NA(2))")
        toilet_col = cols_stripped.get("Community Toilet Complex (including Bath) for General Public (Status A(1)/NA(2))")
        tsc_covered = int((group[tsc_col] == 1).sum()) if tsc_col else 0
        community_toilet = int((group[toilet_col] == 1).sum()) if toilet_col else 0

        # Transport
        national_hwy = int((group["National Highway (Status A(1)/NA(2))"] == 1).sum())
        state_hwy = int((group["State Highway (Status A(1)/NA(2))"] == 1).sum())
        all_weather = int((group["All Weather Road (Status A(1)/NA(2))"] == 1).sum())
        public_bus = int((group["Public Bus Service (Status A(1)/NA(2))"] == 1).sum())
        railway = int((group["Railway Station (Status A(1)/NA(2))"] == 1).sum())

        # Communication
        mobile = int((group["Mobile Phone Coverage (Status A(1)/NA(2))"] == 1).sum())
        internet = int((group["Internet Cafes / Common Service Centre (CSC) (Status A(1)/NA(2))"] == 1).sum())
        post_office = int((group["Post Office (Status A(1)/NA(2))"] == 1).sum())

        # Power
        power_domestic = int((group["Power Supply For Domestic Use  (Status A(1)/NA(2))"] == 1).sum())
        power_agri = int((group["Power Supply For Agriculture Use (Status A(1)/NA(2))"] == 1).sum())

        # Land use
        forest_area = safe_float(group["Forest Area (in Hectares)"])
        net_sown = safe_float(group["Net Area Sown (in Hectares)"])
        non_agri = safe_float(group["Area under Non-Agricultural Uses (in Hectares)"])

        districts[dist_name] = {
            "total_population": total_pop,
            "total_households": total_hh,
            "total_male": total_male,
            "total_female": total_female,
            "total_sc": total_sc,
            "total_st": total_st,
            "total_area_hectares": round(total_area, 2),
            "total_area_sq_km": round(total_area / 100, 2),
            "village_count": n,
            "sex_ratio": round(total_female / max(total_male, 1) * 1000, 1),
            "literacy_proxy": round(total_hh / max(n, 1), 1),  # avg households per village
            "education": {
                "primary_schools": primary_schools,
                "middle_schools": middle_schools,
                "secondary_schools": secondary_schools,
                "sr_sec_schools": sr_sec_schools,
                "degree_colleges": degree_colleges,
                "total_schools": primary_schools + middle_schools + secondary_schools + sr_sec_schools,
                "schools_per_village": round((primary_schools + middle_schools + secondary_schools + sr_sec_schools) / max(n, 1), 2),
            },
            "health": {
                "chc": chc,
                "phc": phc,
                "sub_centres": sub_centre,
                "maternity_centres": maternity,
                "hospitals": hospitals,
                "dispensaries": dispensaries,
                "total_facilities": chc + phc + sub_centre + maternity + hospitals + dispensaries,
                "facilities_per_village": round((chc + phc + sub_centre + maternity + hospitals + dispensaries) / max(n, 1), 3),
            },
            "water": {
                "tap_water_villages": tap_water,
                "hand_pump_villages": hand_pump,
                "tube_well_villages": tube_well,
                "river_canal_villages": river_canal,
                "tank_pond_villages": tank_pond,
                "spring_villages": spring,
                "covered_well_villages": covered_well,
                "pct_tap_water": round(tap_water / max(n, 1) * 100, 1),
                "pct_hand_pump": round(hand_pump / max(n, 1) * 100, 1),
            },
            "drainage": {
                "closed": closed_drainage,
                "open": open_drainage,
                "none": no_drainage,
                "pct_closed": round(closed_drainage / max(n, 1) * 100, 1),
                "pct_none": round(no_drainage / max(n, 1) * 100, 1),
            },
            "sanitation": {
                "tsc_covered_villages": tsc_covered,
                "community_toilets": community_toilet,
                "pct_tsc_covered": round(tsc_covered / max(n, 1) * 100, 1),
            },
            "transport": {
                "national_highway_villages": national_hwy,
                "state_highway_villages": state_hwy,
                "all_weather_road_villages": all_weather,
                "public_bus_villages": public_bus,
                "railway_villages": railway,
                "pct_all_weather": round(all_weather / max(n, 1) * 100, 1),
                "pct_national_hwy": round(national_hwy / max(n, 1) * 100, 1),
            },
            "communication": {
                "mobile_coverage_villages": mobile,
                "internet_csc_villages": internet,
                "post_office_villages": post_office,
                "pct_mobile_coverage": round(mobile / max(n, 1) * 100, 1),
            },
            "power": {
                "domestic_villages": power_domestic,
                "agriculture_villages": power_agri,
                "pct_domestic": round(power_domestic / max(n, 1) * 100, 1),
            },
            "land_use": {
                "forest_hectares": round(forest_area, 2),
                "net_sown_hectares": round(net_sown, 2),
                "non_agri_hectares": round(non_agri, 2),
                "pct_forest": round(forest_area / max(total_area, 1) * 100, 1),
                "pct_agriculture": round(net_sown / max(total_area, 1) * 100, 1),
            },
        }
    return districts


def integrate():
    print("Loading Census 2011 village data...")
    census_df = load_census_villages()
    print(f"  {len(census_df)} Assam villages loaded")

    print("Aggregating to district level...")
    census_districts = aggregate_district(census_df)
    print(f"  {len(census_districts)} districts aggregated")

    # Load assam_data.json
    fp = ASSAM_DIR / "assam_data.json"
    data = json.loads(fp.read_text())

    # District name aliases for matching (newer districts carved from older ones)
    aliases = {
        "tamulpur": "nalbari",
        "bajali": "barpeta",
        "morigaon": "nagaon",
        "majuli": "jorhat",
        "south salmara": "dhubri",
        "biswanath": "sonitpur",
        "charaideo": "sivasagar",
        "hojai": "nagaon",
        "kamrup rural": "kamrup",
        "west karbi anglong": "karbi anglong",
    }

    # Build lowercase lookup for census districts
    census_lower = {c.lower(): c for c in census_districts}

    def match_district(name):
        norm = name.strip().lower()
        alias = aliases.get(norm)
        if alias and alias in census_lower:
            return census_lower[alias]
        if norm in census_lower:
            return census_lower[norm]
        for cl, c in census_lower.items():
            if cl == norm or norm in cl or cl in norm:
                return c
        return None

    matched = 0
    for district in data["districts"]:
        census_name = match_district(district["name"])
        if census_name and census_name in census_districts:
            district["census_2011"] = census_districts[census_name]
            matched += 1

    print(f"\nMatched: {matched}/{len(data['districts'])} districts")

    # Enrich habitations with district-level per-village averages
    for hab in data["habitations"]:
        dist = next((d for d in data["districts"] if d["name"] == hab["district"]), None)
        if dist and "census_2011" in dist:
            c = dist["census_2011"]
            # Scale population to this habitation's share
            dist_total_pop = c["total_population"]
            hab_pop = hab.get("population", 0)
            if dist_total_pop > 0 and hab_pop > 0:
                ratio = hab_pop / dist_total_pop
            else:
                ratio = 1.0 / max(c["village_count"], 1)

            hab["census_2011"] = {
                "district_total_population": c["total_population"],
                "district_total_households": c["total_households"],
                "district_village_count": c["village_count"],
                "estimated_households": int(c["total_households"] * ratio),
                "sex_ratio": c["sex_ratio"],
                "sc_pct": round(c["total_sc"] / max(c["total_population"], 1) * 100, 1),
                "st_pct": round(c["total_st"] / max(c["total_population"], 1) * 100, 1),
                "education": c["education"],
                "health": c["health"],
                "water": c["water"],
                "drainage": c["drainage"],
                "sanitation": c["sanitation"],
                "transport": c["transport"],
                "communication": c["communication"],
                "power": c["power"],
                "land_use": c["land_use"],
            }

    # Save
    fp.write_text(json.dumps(data, indent=2))
    print(f"Saved to {fp}")

    # Print sample
    print("\nSample enriched district:")
    for d in data["districts"]:
        if "census_2011" in d:
            c = d["census_2011"]
            print(f"  {d['name']}: pop={c['total_population']}, villages={c['village_count']}, "
                  f"schools={c['education']['total_schools']}, health={c['health']['total_facilities']}, "
                  f"mobile={c['communication']['pct_mobile_coverage']}%")
            break


if __name__ == "__main__":
    integrate()
