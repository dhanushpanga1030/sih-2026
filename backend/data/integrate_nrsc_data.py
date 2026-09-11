"""Integrate real NRSC/ISRO Flood Hazard Zonation data into SafeHabitat AI.

Source: Flood Hazard Zonation Atlas of Assam (1998-2023)
NRSC/ISRO & NDMA & ASDMA
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent

# Table 5.3: District-wise villages under each hazard category
# Table 5.4: District-wise Flood Hazard Ranking Index
NRSC_FLOOD_DATA = {
    "Bajali": {
        "very_high": 18,
        "high": 19,
        "moderate": 28,
        "low": 16,
        "very_low": 72,
        "ranking": "II",
        "index": 26,
        "gauge_station": None,
        "flood_waves": 26,
    },
    "Baksa": {
        "very_high": 1,
        "high": 9,
        "moderate": 21,
        "low": 12,
        "very_low": 311,
        "ranking": "III",
        "index": 16,
        "gauge_station": None,
        "flood_waves": 16,
    },
    "Barpeta": {
        "very_high": 129,
        "high": 105,
        "moderate": 87,
        "low": 32,
        "very_low": 160,
        "ranking": "I",
        "index": 57,
        "gauge_station": "NH R.d xing (Manas)",
        "flood_waves": 25,
    },
    "Biswanath": {
        "very_high": 47,
        "high": 29,
        "moderate": 44,
        "low": 37,
        "very_low": 184,
        "ranking": "III",
        "index": 16,
        "gauge_station": None,
        "flood_waves": 16,
    },
    "Bongaigaon": {
        "very_high": 51,
        "high": 20,
        "moderate": 31,
        "low": 19,
        "very_low": 351,
        "ranking": "III",
        "index": 16,
        "gauge_station": None,
        "flood_waves": 16,
    },
    "Cachar": {
        "very_high": 224,
        "high": 25,
        "moderate": 72,
        "low": 34,
        "very_low": 381,
        "ranking": "I",
        "index": 45,
        "gauge_station": "A.P. Ghat / B.P. Ghat",
        "flood_waves": 23,
    },
    "Charaideo": {
        "very_high": 4,
        "high": 5,
        "moderate": 24,
        "low": 13,
        "very_low": 262,
        "ranking": "III",
        "index": 19,
        "gauge_station": None,
        "flood_waves": 19,
    },
    "Chirang": {
        "very_high": 10,
        "high": 3,
        "moderate": 3,
        "low": 5,
        "very_low": 336,
        "ranking": "III",
        "index": 15,
        "gauge_station": None,
        "flood_waves": 15,
    },
    "Darrang": {
        "very_high": 50,
        "high": 23,
        "moderate": 40,
        "low": 44,
        "very_low": 317,
        "ranking": "III",
        "index": 18,
        "gauge_station": None,
        "flood_waves": 18,
    },
    "Dhemaji": {
        "very_high": 15,
        "high": 20,
        "moderate": 76,
        "low": 113,
        "very_low": 367,
        "ranking": "II",
        "index": 22,
        "gauge_station": "NH-52 RCC Bridge",
        "flood_waves": 22,
    },
    "Dhubri": {
        "very_high": 185,
        "high": 53,
        "moderate": 111,
        "low": 0,
        "very_low": 0,
        "ranking": "I",
        "index": 48,
        "gauge_station": "Dhubri / Golokganj",
        "flood_waves": 63,
    },
    "Dibrugarh": {
        "very_high": 97,
        "high": 56,
        "moderate": 146,
        "low": 94,
        "very_low": 863,
        "ranking": "I",
        "index": 48,
        "gauge_station": "Dibrugarh / Naharkatia / Khowang",
        "flood_waves": 116,
    },
    "Dima Hasao": {
        "very_high": 0,
        "high": 0,
        "moderate": 0,
        "low": 0,
        "very_low": 6,
        "ranking": "III",
        "index": 15,
        "gauge_station": None,
        "flood_waves": 15,
    },
    "Goalpara": {
        "very_high": 144,
        "high": 64,
        "moderate": 76,
        "low": 33,
        "very_low": 378,
        "ranking": "I",
        "index": 45,
        "gauge_station": "Goalpara",
        "flood_waves": 31,
    },
    "Golaghat": {
        "very_high": 35,
        "high": 37,
        "moderate": 40,
        "low": 31,
        "very_low": 412,
        "ranking": "I",
        "index": 51,
        "gauge_station": "Golaghat",
        "flood_waves": 39,
    },
    "Hailakandi": {
        "very_high": 59,
        "high": 8,
        "moderate": 8,
        "low": 16,
        "very_low": 194,
        "ranking": "I",
        "index": 48,
        "gauge_station": "Matizuri",
        "flood_waves": 54,
    },
    "Hojai": {
        "very_high": 63,
        "high": 21,
        "moderate": 62,
        "low": 24,
        "very_low": 121,
        "ranking": "II",
        "index": 21,
        "gauge_station": None,
        "flood_waves": 21,
    },
    "Jorhat": {
        "very_high": 39,
        "high": 13,
        "moderate": 46,
        "low": 35,
        "very_low": 287,
        "ranking": "I",
        "index": 54,
        "gauge_station": "Neamatighat",
        "flood_waves": 133,
    },
    "Kamrup Metro": {
        "very_high": 42,
        "high": 4,
        "moderate": 14,
        "low": 8,
        "very_low": 77,
        "ranking": "I",
        "index": 45,
        "gauge_station": "Guwahati D.C. Court",
        "flood_waves": 36,
    },
    "Kamrup Rural": {
        "very_high": 47,
        "high": 12,
        "moderate": 0,
        "low": 0,
        "very_low": 0,
        "ranking": "I",
        "index": 48,
        "gauge_station": "N.H.Rd xing (Puthimari)",
        "flood_waves": 81,
    },
    "Karbi Anglong": {
        "very_high": 0,
        "high": 0,
        "moderate": 0,
        "low": 0,
        "very_low": 3,
        "ranking": "III",
        "index": 15,
        "gauge_station": None,
        "flood_waves": 15,
    },
    "Karimganj": {
        "very_high": 117,
        "high": 34,
        "moderate": 30,
        "low": 46,
        "very_low": 201,
        "ranking": "I",
        "index": 48,
        "gauge_station": "Karimganj",
        "flood_waves": 58,
    },
    "Kokrajhar": {
        "very_high": 21,
        "high": 5,
        "moderate": 8,
        "low": 13,
        "very_low": 203,
        "ranking": "III",
        "index": 16,
        "gauge_station": "Kokrajhar",
        "flood_waves": 16,
    },
    "Lakhimpur": {
        "very_high": 56,
        "high": 63,
        "moderate": 107,
        "low": 92,
        "very_low": 651,
        "ranking": "I",
        "index": 44,
        "gauge_station": "Badatighat / Chouldhowa ghat",
        "flood_waves": 11,
    },
    "Majuli": {
        "very_high": 22,
        "high": 21,
        "moderate": 41,
        "low": 18,
        "very_low": 38,
        "ranking": "III",
        "index": 18,
        "gauge_station": None,
        "flood_waves": 18,
    },
    "Morigaon": {
        "very_high": 117,
        "high": 58,
        "moderate": 93,
        "low": 49,
        "very_low": 146,
        "ranking": "I",
        "index": 105,
        "gauge_station": "Dharamtul",
        "flood_waves": 26,
    },
    "Nagaon": {
        "very_high": 105,
        "high": 46,
        "moderate": 84,
        "low": 61,
        "very_low": 501,
        "ranking": "I",
        "index": 66,
        "gauge_station": "Kampur",
        "flood_waves": 42,
    },
    "Nalbari": {
        "very_high": 28,
        "high": 40,
        "moderate": 71,
        "low": 17,
        "very_low": 348,
        "ranking": "I",
        "index": 66,
        "gauge_station": "N.T.Rd.xing - Pagaladiya",
        "flood_waves": 28,
    },
    "Sivasagar": {
        "very_high": 89,
        "high": 7,
        "moderate": 29,
        "low": 18,
        "very_low": 113,
        "ranking": "I",
        "index": 81,
        "gauge_station": "Sibsagar / Nanglamor ghat",
        "flood_waves": 67,
    },
    "Sonitpur": {
        "very_high": 21,
        "high": 16,
        "moderate": 51,
        "low": 39,
        "very_low": 424,
        "ranking": "I",
        "index": 48,
        "gauge_station": "Tejpur / N.T.RD Xing",
        "flood_waves": 63,
    },
    "South Salmara": {
        "very_high": 34,
        "high": 20,
        "moderate": 37,
        "low": 0,
        "very_low": 0,
        "ranking": "II",
        "index": 25,
        "gauge_station": None,
        "flood_waves": 25,
    },
    "Tamulpur": {
        "very_high": 0,
        "high": 1,
        "moderate": 2,
        "low": 10,
        "very_low": 243,
        "ranking": "III",
        "index": 17,
        "gauge_station": None,
        "flood_waves": 17,
    },
    "Tinsukia": {
        "very_high": 4,
        "high": 8,
        "moderate": 23,
        "low": 35,
        "very_low": 451,
        "ranking": "III",
        "index": 17,
        "gauge_station": "Dolabazar",
        "flood_waves": 2,
    },
    "Udalguri": {
        "very_high": 0,
        "high": 0,
        "moderate": 14,
        "low": 14,
        "very_low": 597,
        "ranking": "III",
        "index": 17,
        "gauge_station": None,
        "flood_waves": 17,
    },
    "West Karbi Anglong": {
        "very_high": 0,
        "high": 0,
        "moderate": 0,
        "low": 0,
        "very_low": 3,
        "ranking": "III",
        "index": 15,
        "gauge_station": None,
        "flood_waves": 15,
    },
}

# Table 5.1: Overall flood hazard statistics
STATE_FLOOD_SUMMARY = {
    "very_high_ha": 326522,
    "high_ha": 286886,
    "moderate_ha": 465765,
    "low_ha": 532891,
    "very_low_ha": 1096239,
    "total_flood_affected_ha": 2708302,
    "state_geographic_area_ha": 7843800,
    "pct_state_affected": 34.5,
    "data_source": "NRSC/ISRO Flood Hazard Zonation Atlas of Assam (1998-2023)",
    "satellite_datasets": 389,
    "years_analyzed": 26,
    "spatial_resolution": "50m x 50m",
    "validation_accuracy": "81% match with field reports",
}


def compute_flood_risk_score(district_name: str) -> dict:
    """Compute ML-ready flood risk score from NRSC data."""
    data = NRSC_FLOOD_DATA.get(district_name)
    if not data:
        return {"flood_risk": 0.3, "confidence": 0.5, "method": "no_data"}

    total_villages = (
        data["very_high"] + data["high"] + data["moderate"] + data["low"] + data["very_low"]
    )
    if total_villages == 0:
        return {"flood_risk": 0.1, "confidence": 0.4, "method": "no_villages"}

    # Weighted flood risk: very_high=1.0, high=0.8, moderate=0.5, low=0.3, very_low=0.1
    weighted = (
        data["very_high"] * 1.0
        + data["high"] * 0.8
        + data["moderate"] * 0.5
        + data["low"] * 0.3
        + data["very_low"] * 0.1
    )
    flood_risk = round(weighted / total_villages, 3)

    # Confidence based on data completeness
    has_gauge = 1 if data["gauge_station"] else 0
    confidence = round(0.70 + has_gauge * 0.15 + min(data["very_high"] / 100, 0.15), 2)

    return {
        "flood_risk": flood_risk,
        "confidence": confidence,
        "method": "nrsc_satellite_1998_2023",
        "very_high_villages": data["very_high"],
        "high_villages": data["high"],
        "moderate_villages": data["moderate"],
        "low_villages": data["low"],
        "very_low_villages": data["very_low"],
        "total_villages": total_villages,
        "ranking": data["ranking"],
        "hazard_index": data["index"],
        "flood_waves": data["flood_waves"],
        "gauge_station": data["gauge_station"],
    }


def update_assam_data():
    """Update assam_data.json with real NRSC flood data."""
    fp = DATA_DIR / "assam" / "assam_data.json"
    data = json.loads(fp.read_text())

    for district in data["districts"]:
        name = district["name"]
        nrsc = compute_flood_risk_score(name)
        district["nrsc_flood_data"] = nrsc

        # Update habitations in this district
        for hab in data["habitations"]:
            if hab["district"] == name:
                # Override synthetic flood score with NRSC data
                old_flood = hab["hazard"]["flood"]
                new_flood = nrsc["flood_risk"]
                hab["hazard"]["flood"] = new_flood
                hab["hazard"]["flood_source"] = "NRSC/ISRO 1998-2023"
                hab["hazard"]["flood_confidence"] = nrsc["confidence"]

                # Recompute combined hazard
                hab["hazard"]["combined"] = round(
                    0.35 * new_flood
                    + 0.25 * hab["hazard"]["landslide"]
                    + 0.25 * hab["hazard"]["seismic"]
                    + 0.15 * hab["hazard"]["erosion"],
                    3,
                )

                # Recompute risk
                old_risk = hab["risk"]["overall"]
                new_risk = round(
                    0.4 * hab["hazard"]["combined"]
                    + 0.3 * hab["vulnerability"]["combined"]
                    + 0.3 * hab["exposure"],
                    3,
                )
                hab["risk"]["overall"] = new_risk

                if new_risk >= 0.65:
                    hab["risk"]["band"] = "immediate"
                elif new_risk >= 0.50:
                    hab["risk"]["band"] = "short_term"
                elif new_risk >= 0.35:
                    hab["risk"]["band"] = "medium_term"
                else:
                    hab["risk"]["band"] = "monitor"

                hab["risk"]["data_source"] = "NRSC/ISRO Flood Hazard Zonation Atlas (1998-2023)"

    # Add metadata
    data["nrsc_metadata"] = STATE_FLOOD_SUMMARY

    fp.write_text(json.dumps(data, indent=2))

    # Print summary
    bands = {}
    for h in data["habitations"]:
        b = h["risk"]["band"]
        bands[b] = bands.get(b, 0) + 1

    print(f"Updated {len(data['districts'])} districts with NRSC flood data")
    print(f"Updated {len(data['habitations'])} habitations")
    print(f"New band distribution: {bands}")
    print(f"Data source: {STATE_FLOOD_SUMMARY['data_source']}")


if __name__ == "__main__":
    update_assam_data()
