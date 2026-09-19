"""Enrich habitation data with real IMD rainfall features.

Uses strict outlier filtering (Assam annual rainfall is 1500-3500mm)
and falls back to regional averages for corrupted stations.
"""
import json
import math
import statistics
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "assam"
RAINFALL_JSON = DATA_DIR / "rainfall_real.json"
ASSAM_JSON = DATA_DIR / "assam_data.json"

# Assam reasonable bounds
MAX_ANNUAL_MM = 4000
MAX_MONTHLY_MM = 1200
ASSAM_REGIONAL_ANNUAL = 2100  # mm, Assam average
ASSAM_MONSOON_FRACTION = 0.65  # ~65% of annual falls Jun-Sep


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def find_nearest_station(hab_lat, hab_lon, stations, max_dist_km=100):
    best, best_dist = None, max_dist_km
    for st in stations:
        d = haversine_km(hab_lat, hab_lon, st["lat"], st["lon"])
        if d < best_dist:
            best_dist, best = d, st
    return best, best_dist


def compute_features(monthly_dict: dict, station_count: int):
    """Compute rainfall features with strict outlier capping."""
    sc = max(station_count, 1)

    # Per-station monthly values
    per_station = [v / sc for v in monthly_dict.values()]

    # Cap individual values
    capped = [min(v, MAX_MONTHLY_MM) for v in per_station]

    # Compute from annual totals if available and reasonable
    # Group by year
    by_year = {}
    for mk, mv in monthly_dict.items():
        yr = mk.split("-")[0]
        by_year.setdefault(yr, []).append(mv / sc)

    # Per-year totals (capped monthly)
    year_totals = []
    for yr, vals in by_year.items():
        capped_yr = [min(v, MAX_MONTHLY_MM) for v in vals]
        yr_total = sum(capped_yr)
        if yr_total <= MAX_ANNUAL_MM * 2:  # allow some slack
            year_totals.append(yr_total)

    if year_totals:
        annual_avg = statistics.median(year_totals)
    else:
        annual_avg = ASSAM_REGIONAL_ANNUAL

    # Monsoon: average of Jun-Sep months (capped)
    monsoon_months = ["06", "07", "08", "09"]
    by_month = {}
    for mk, mv in monthly_dict.items():
        mn = mk.split("-")[1]
        by_month.setdefault(mn, []).append(mv / sc)

    monsoon_vals = []
    for m in monsoon_months:
        if m in by_month:
            vals = [min(v, MAX_MONTHLY_MM) for v in by_month[m]]
            monsoon_vals.append(statistics.median(vals))

    monsoon_total = sum(monsoon_vals) if monsoon_vals else annual_avg * ASSAM_MONSOON_FRACTION
    monsoon_pct = round(monsoon_total / max(annual_avg, 1) * 100, 1)

    # Max single month (median of each month's values, then max)
    month_medians = []
    for m, vals in by_month.items():
        capped_vals = [min(v, MAX_MONTHLY_MM) for v in vals]
        month_medians.append(statistics.median(capped_vals))
    max_monthly = max(month_medians) if month_medians else 0

    return {
        "annual_mm": round(annual_avg, 1),
        "max_monthly_mm": round(max_monthly, 1),
        "monsoon_mm": round(monsoon_total, 1),
        "monsoon_pct": monsoon_pct,
    }


def enrich():
    rainfall = json.loads(RAINFALL_JSON.read_text())
    assam = json.loads(ASSAM_JSON.read_text())

    tel = rainfall.get("telemetry_hourly_rainfall", {})
    manual = rainfall.get("manual_daily_rainfall", {})
    rwl = rainfall.get("river_water_level", {})

    # Build station list from both telemetry AND manual
    stations = []
    for dist, d in tel.items():
        sc = d.get("station_count", 1)
        for st_name in d.get("stations", []):
            stations.append({
                "name": st_name, "district": dist,
                "lat": d["lat"], "lon": d["lon"],
                "monthly": d.get("monthly_rainfall_mm", {}),
                "station_count": sc, "source": "telemetry",
            })
    # Manual data lacks lat/lon — only use telemetry for location-based matching.
    # Manual data can be used as a quality cross-check if needed later.

    print(f"Stations: {len(stations)} (telemetry)")
    print(f"Habitations: {len(assam['habitations'])}")

    matched = unmatched = 0
    for hab in assam["habitations"]:
        hlat, hlon = hab.get("lat", 0), hab.get("lon", 0)
        if hlat == 0 or hlon == 0:
            unmatched += 1
            hab["real_rainfall"] = _empty()
            continue

        nearest, dist_km = find_nearest_station(hlat, hlon, stations)
        if nearest is None:
            unmatched += 1
            hab["real_rainfall"] = _empty()
            continue

        matched += 1
        feat = compute_features(nearest["monthly"], nearest["station_count"])
        rwl_data = rwl.get(nearest["district"], {})

        hab["real_rainfall"] = {
            "rainfall_annual_mm": feat["annual_mm"],
            "rainfall_max_monthly_mm": feat["max_monthly_mm"],
            "rainfall_monsoon_mm": feat["monsoon_mm"],
            "rainfall_monsoon_pct": feat["monsoon_pct"],
            "rainfall_station": nearest["name"],
            "rainfall_station_distance_km": round(dist_km, 1),
            "river_water_level_max_m": rwl_data.get("max_level_m", 0),
        }

    print(f"Matched: {matched}, Unmatched: {unmatched}")
    ASSAM_JSON.write_text(json.dumps(assam, indent=2))
    print(f"Saved to {ASSAM_JSON}")

    # Stats
    annuals = [h["real_rainfall"]["rainfall_annual_mm"] for h in assam["habitations"]
               if h["real_rainfall"]["rainfall_station"]]
    print(f"\nRainfall stats across {len(annuals)} habitations:")
    print(f"  Annual: min={min(annuals):.0f}, median={statistics.median(annuals):.0f}, max={max(annuals):.0f} mm")


def _empty():
    return {
        "rainfall_annual_mm": 0, "rainfall_max_monthly_mm": 0,
        "rainfall_monsoon_mm": 0, "rainfall_monsoon_pct": 0,
        "rainfall_station": "", "rainfall_station_distance_km": 0,
        "river_water_level_max_m": 0,
    }


if __name__ == "__main__":
    enrich()
