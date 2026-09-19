"""Real Rainfall & River Water Level Data Ingestion.

Preads:
- rainfall_tel_hr_assam_as_*.csv  (Telemetry Hourly Rainfall)
- rainfall_manual_daily_assam_as_*.csv  (Manual Daily Rainfall)
- rwl_tel_hr_assam_999_*.csv  (River Water Level Telemetry)

Aggregates by district → monthly totals, annual stats, station metadata.
Outputs JSON for API consumption.
"""
import csv
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

DATA_DIR = Path(__file__).parent.parent.parent / "data"
REAL_DIR = DATA_DIR / "real_datasets"
OUTPUT = DATA_DIR / "assam" / "rainfall_real.json"

# ── Helpers ──────────────────────────────────────────────────────────────

def parse_timestamp(ts: str) -> datetime | None:
    """Parse 'DD-MM-YYYY HH:MM' format."""
    try:
        return datetime.strptime(ts.strip(), "%d-%m-%Y %H:%M")
    except Exception:
        return None


def month_key(dt: datetime) -> str:
    return dt.strftime("%Y-%m")


def year_key(dt: datetime) -> str:
    return dt.strftime("%Y")


# ── Telemetry Hourly Rainfall ────────────────────────────────────────────

def load_tel_hourlyRainfall() -> dict:
    """Parse hourly telemetry rainfall CSVs and aggregate by district."""
    files = sorted(REAL_DIR.glob("rainfall_tel_hr_assam_as_*.csv"))
    districts: dict[str, dict] = defaultdict(lambda: {
        "stations": set(),
        "monthly": defaultdict(float),
        "hourly_events": 0,
        "total_mm": 0.0,
        "max_hourly_mm": 0.0,
        "lat": 0.0,
        "lon": 0.0,
        "n_records": 0,
        "years": set(),
    })

    for fp in files:
        with open(fp, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                dist = row.get("District", "").strip()
                if not dist:
                    continue
                d = districts[dist]
                d["stations"].add(row.get("Station", "").strip())
                d["n_records"] += 1

                try:
                    rainfall = float(row.get("Telemetry Hourly Rainfall (mm)", 0) or 0)
                except (ValueError, TypeError):
                    rainfall = 0.0

                d["total_mm"] += rainfall
                if rainfall > d["max_hourly_mm"]:
                    d["max_hourly_mm"] = rainfall

                if rainfall > 0:
                    d["hourly_events"] += 1

                dt = parse_timestamp(row.get("Data Acquisition Time", ""))
                if dt:
                    d["monthly"][month_key(dt)] += rainfall
                    d["years"].add(year_key(dt))
                    lat = float(row.get("Latitude", 0) or 0)
                    lon = float(row.get("Longitude", 0) or 0)
                    if lat != 0:
                        d["lat"] = lat
                    if lon != 0:
                        d["lon"] = lon

    # Serialize
    result = {}
    for dist, d in districts.items():
        monthly_sorted = dict(sorted(d["monthly"].items()))
        annual = defaultdict(float)
        for mk, mv in monthly_sorted.items():
            annual[mk[:4]] += mv

        result[dist] = {
            "district": dist,
            "station_count": len(d["stations"]),
            "stations": sorted(d["stations"]),
            "total_mm": round(d["total_mm"], 1),
            "max_hourly_mm": round(d["max_hourly_mm"], 1),
            "hourly_rainfall_events": d["hourly_events"],
            "n_records": d["n_records"],
            "monthly_rainfall_mm": {k: round(v, 1) for k, v in monthly_sorted.items()},
            "annual_rainfall_mm": {k: round(v, 1) for k, v in sorted(annual.items())},
            "lat": round(d["lat"], 6),
            "lon": round(d["lon"], 6),
            "years_covered": sorted(d["years"]),
        }
    return result


# ── Manual Daily Rainfall ────────────────────────────────────────────────

def load_manual_daily_rainfall() -> dict:
    """Parse manual daily rainfall CSVs."""
    files = sorted(REAL_DIR.glob("rainfall_manual_daily_assam_as_*.csv"))
    districts: dict[str, dict] = defaultdict(lambda: {
        "stations": set(),
        "monthly": defaultdict(float),
        "total_mm": 0.0,
        "max_daily_mm": 0.0,
        "n_records": 0,
    })

    for fp in files:
        with open(fp, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                dist = row.get("District", "").strip()
                if not dist:
                    continue
                d = districts[dist]
                d["stations"].add(row.get("Station", "").strip())
                d["n_records"] += 1

                try:
                    rainfall = float(row.get("Manual Daily Rainfall (mm)", 0) or 0)
                except (ValueError, TypeError):
                    rainfall = 0.0

                d["total_mm"] += rainfall
                if rainfall > d["max_daily_mm"]:
                    d["max_daily_mm"] = rainfall

                dt = parse_timestamp(row.get("Data Acquisition Time", ""))
                if dt:
                    d["monthly"][month_key(dt)] += rainfall

    result = {}
    for dist, d in districts.items():
        monthly_sorted = dict(sorted(d["monthly"].items()))
        result[dist] = {
            "district": dist,
            "station_count": len(d["stations"]),
            "stations": sorted(d["stations"]),
            "total_mm": round(d["total_mm"], 1),
            "max_daily_mm": round(d["max_daily_mm"], 1),
            "n_records": d["n_records"],
            "monthly_rainfall_mm": {k: round(v, 1) for k, v in monthly_sorted.items()},
        }
    return result


# ── River Water Level ────────────────────────────────────────────────────

def load_river_water_level() -> dict:
    """Parse river water level telemetry CSVs."""
    files = sorted(REAL_DIR.glob("rwl_tel_hr_assam_999_*.csv"))
    districts: dict[str, dict] = defaultdict(lambda: {
        "stations": set(),
        "monthly_avg": defaultdict(list),
        "max_level_m": 0.0,
        "min_level_m": 999.0,
        "n_records": 0,
    })

    for fp in files:
        with open(fp, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                dist = row.get("District", "").strip()
                if not dist:
                    continue
                d = districts[dist]
                d["stations"].add(row.get("Station", "").strip())
                d["n_records"] += 1

                try:
                    level = float(row.get("River Water Level Telemetry Hourly (meter)", 0) or 0)
                except (ValueError, TypeError):
                    level = 0.0

                if level > d["max_level_m"]:
                    d["max_level_m"] = level
                if level > 0 and level < d["min_level_m"]:
                    d["min_level_m"] = level

                dt = parse_timestamp(row.get("Data Acquisition Time", ""))
                if dt and level > 0:
                    d["monthly_avg"][month_key(dt)].append(level)

    result = {}
    for dist, d in districts.items():
        monthly_avg = {
            k: round(sum(v) / len(v), 3)
            for k, v in sorted(d["monthly_avg"].items())
        }
        result[dist] = {
            "district": dist,
            "station_count": len(d["stations"]),
            "stations": sorted(d["stations"]),
            "max_level_m": round(d["max_level_m"], 3),
            "min_level_m": round(d["min_level_m"], 3) if d["min_level_m"] < 999 else 0,
            "n_records": d["n_records"],
            "monthly_avg_level_m": monthly_avg,
        }
    return result


# ── Main ─────────────────────────────────────────────────────────────────

def ingest_all():
    print("Ingesting real rainfall data...")
    tel = load_tel_hourlyRainfall()
    print(f"  Telemetry hourly: {len(tel)} districts")

    manual = load_manual_daily_rainfall()
    print(f"  Manual daily: {len(manual)} districts")

    rwl = load_river_water_level()
    print(f"  River water level: {len(rwl)} districts")

    output = {
        "metadata": {
            "description": "Real rainfall and river water level data from Assam",
            "sources": [
                "IMD Telemetry Hourly Rainfall (2021-2025, 2026-2030)",
                "IMD Manual Daily Rainfall (2021-2025)",
                "River Water Level Telemetry (2021-2025)",
            ],
            "generated_at": datetime.now().isoformat(),
        },
        "telemetry_hourly_rainfall": tel,
        "manual_daily_rainfall": manual,
        "river_water_level": rwl,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, indent=2))
    print(f"\nSaved to {OUTPUT}")
    print(f"  Districts with rainfall data: {len(tel)}")
    print(f"  Districts with river data: {len(rwl)}")

    # Summary
    total_records = sum(d["n_records"] for d in tel.values())
    total_mm = sum(d["total_mm"] for d in tel.values())
    print(f"  Total rainfall records: {total_records:,}")
    print(f"  Total rainfall measured: {total_mm:,.0f} mm")


if __name__ == "__main__":
    ingest_all()
