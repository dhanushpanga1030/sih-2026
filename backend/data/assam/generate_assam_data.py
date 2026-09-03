import json
import random
import math
from pathlib import Path

# Assam districts with rough lat/long centers and hazard profiles
ASSAM_DISTRICTS = [
    {"name": "Kamrup Metropolitan", "lat": 26.14, "lon": 91.74, "flood_risk": 0.8, "seismic_zone": 5},
    {"name": "Kamrup Rural", "lat": 26.20, "lon": 90.80, "flood_risk": 0.7, "seismic_zone": 5},
    {"name": "Nagaon", "lat": 26.35, "lon": 92.68, "flood_risk": 0.75, "seismic_zone": 5},
    {"name": "Jorhat", "lat": 26.75, "lon": 94.20, "flood_risk": 0.6, "seismic_zone": 5},
    {"name": "Dibrugarh", "lat": 27.47, "lon": 94.91, "flood_risk": 0.65, "seismic_zone": 5},
    {"name": "Tinsukia", "lat": 27.49, "lon": 95.36, "flood_risk": 0.55, "seismic_zone": 5},
    {"name": "Sonitpur", "lat": 26.75, "lon": 92.80, "flood_risk": 0.7, "seismic_zone": 5},
    {"name": "Lakhimpur", "lat": 27.24, "lon": 94.10, "flood_risk": 0.72, "seismic_zone": 5},
    {"name": "Golaghat", "lat": 26.51, "lon": 93.96, "flood_risk": 0.5, "seismic_zone": 5},
    {"name": "Sivasagar", "lat": 26.98, "lon": 94.63, "flood_risk": 0.55, "seismic_zone": 5},
    {"name": "Dhemaji", "lat": 27.47, "lon": 94.58, "flood_risk": 0.85, "seismic_zone": 5},
    {"name": "Dima Hasao", "lat": 25.50, "lon": 93.20, "flood_risk": 0.3, "seismic_zone": 5, "landslide_risk": 0.8},
    {"name": "Karbi Anglong", "lat": 26.00, "lon": 93.50, "flood_risk": 0.25, "seismic_zone": 5, "landslide_risk": 0.6},
    {"name": "Cachar", "lat": 24.80, "lon": 92.85, "flood_risk": 0.65, "seismic_zone": 5},
    {"name": "Hailakandi", "lat": 24.68, "lon": 92.56, "flood_risk": 0.6, "seismic_zone": 5},
    {"name": "Karimganj", "lat": 24.87, "lon": 92.35, "flood_risk": 0.7, "seismic_zone": 5},
    {"name": "Morigaon", "lat": 26.25, "lon": 92.35, "flood_risk": 0.78, "seismic_zone": 5},
    {"name": "Nalbari", "lat": 26.44, "lon": 91.44, "flood_risk": 0.73, "seismic_zone": 5},
    {"name": "Barpeta", "lat": 26.32, "lon": 91.00, "flood_risk": 0.76, "seismic_zone": 5},
    {"name": "Kokrajhar", "lat": 26.40, "lon": 90.27, "flood_risk": 0.68, "seismic_zone": 5},
    {"name": "Chirang", "lat": 26.45, "lon": 90.45, "flood_risk": 0.65, "seismic_zone": 5},
    {"name": "Bongaigaon", "lat": 26.47, "lon": 90.56, "flood_risk": 0.67, "seismic_zone": 5},
    {"name": "Dhubri", "lat": 26.02, "lon": 90.00, "flood_risk": 0.82, "seismic_zone": 5},
    {"name": "Goalpara", "lat": 26.17, "lon": 90.62, "flood_risk": 0.71, "seismic_zone": 5},
    {"name": "Majuli", "lat": 26.95, "lon": 94.00, "flood_risk": 0.9, "seismic_zone": 5},
    {"name": "South Salmara", "lat": 25.90, "lon": 90.05, "flood_risk": 0.88, "seismic_zone": 5},
    {"name": "Biswanath", "lat": 26.80, "lon": 93.15, "flood_risk": 0.62, "seismic_zone": 5},
    {"name": "Charaideo", "lat": 27.10, "lon": 94.80, "flood_risk": 0.5, "seismic_zone": 5},
    {"name": "Hojai", "lat": 26.00, "lon": 92.85, "flood_risk": 0.6, "seismic_zone": 5},
    {"name": "West Karbi Anglong", "lat": 26.15, "lon": 93.10, "flood_risk": 0.2, "seismic_zone": 5, "landslide_risk": 0.5},
    {"name": "Baksa", "lat": 26.55, "lon": 90.70, "flood_risk": 0.6, "seismic_zone": 5},
    {"name": "Udalguri", "lat": 26.75, "lon": 92.10, "flood_risk": 0.55, "seismic_zone": 5},
    {"name": "Tamulpur", "lat": 26.65, "lon": 91.90, "flood_risk": 0.58, "seismic_zone": 5},
    {"name": "Bajali", "lat": 26.45, "lon": 91.20, "flood_risk": 0.41, "seismic_zone": 5},
    {"name": "Darrang", "lat": 26.65, "lon": 92.10, "flood_risk": 0.35, "seismic_zone": 5},
]

random.seed(42)

HABITATION_NAMES = [
    "Bamunigaon", "Goalpara Gaon", "Chapaguri", "Bishnupur", "Narayanpur",
    "Rangia Town", "Kamalpur", "Hajo", "Sualkuchi", "Palasbari",
    "Mangaldai Town", "Sidhpur", "Kharupetia", "Dalgaon", "Puthimari",
    "North Salmara", "Boginadi", "Gohpur", "Biswanath Chariali", "Tezpur Town",
    "Jorhat Town", "Golaghat Town", "Titabor", "Margherita", "Digboi Town",
    "Dibrugarh Town", "Tinsukia Town", "Sadiya", "Dhemaji Town", "Jonai",
    "Silchar Town", "Hailakandi Town", "Karimganj Town", "Badarpur",
    "Haflong Town", "Maibong", "Lumding", "Hojai Town", "Nagaon Town",
    "Morigaon Town", "Jagiroad", "Nalbari Town", "Barpeta Town", "Pathsala",
    "Kokrajhar Town", "Chapaguri", "Bongaigaon Town", "Dhubri Town",
    "Goalpara Town", "Bilasipara", "Majuli Island", "Jorhat Chariali",
    "Demow", "Nazira", "Sonari", "Amguri", "Na-Dih",
    "Jalukbari", "Azara", "Beltola", "Dispur", "GS Road",
    "Fatasil", "Lachitgarh", "Chouldhury", "Kumarikata", "Baska",
    "Baghmara", "Rakhaldubi", "Kheroni", "Lungru", "Chingra",
    "Diphu Town", "Bokajan", "Hamren", "Koppara", "Tengakhat",
    "Silonijan", "Makum", "Tingkhong", "Chabua", "Lakhimpur Town",
    "North Lakhimpur", "Dhakuakhana", "Ghagarichadi", "Naobicha", "Jengraimukh",
    "Mariani", "Rupai", "Sapekhati", "Khowang", "Naharkatia",
    "Badatop", "Borhola", "leticombuj", "Jamuna", "Lakhiganj",
    "Bhuragaon", "Patacharkuchi", "Sarukhetri", "Barpeta Road", "Howly",
    "Bilasipara", "Gossaigaon", "Fakiragram", "Mancachar", "Sapatgram",
    "Bhergaon", "Udalguri Town", "Mazbat", "Harisinga", "Bhairabkunda",
]

DISTRICT_POPULATIONS = {
    "Kamrup Metropolitan": 1200000, "Kamrup Rural": 1800000, "Nagaon": 2500000,
    "Jorhat": 1100000, "Dibrugarh": 1400000, "Tinsukia": 900000,
    "Sonitpur": 1300000, "Lakhimpur": 1100000, "Golaghat": 1100000,
    "Sivasagar": 1200000, "Dhemaji": 700000, "Dima Hasao": 250000,
    "Karbi Anglong": 450000, "Cachar": 1800000, "Hailakandi": 700000,
    "Karimganj": 1300000, "Morigaon": 1000000, "Nalbari": 800000,
    "Barpeta": 1700000, "Kokrajhar": 900000, "Chirang": 500000,
    "Bongaigaon": 700000, "Dhubri": 1600000, "Goalpara": 1100000,
    "Majuli": 170000, "South Salmara": 400000, "Biswanath": 600000,
    "Charaideo": 500000, "Hojai": 900000, "West Karbi Anglong": 200000,
    "Baksa": 500000, "Udalguri": 600000, "Tamulpur": 400000,
    "Bajali": 500000, "Darrang": 700000,
}


def jitter(val, pct=0.05):
    return round(val * (1 + random.uniform(-pct, pct)), 4)


def gen_habitations(district, n=5):
    pop_total = DISTRICT_POPULATIONS.get(district["name"], 800000)
    hab_pop = pop_total // n
    habitations = []
    for i in range(n):
        angle = 2 * math.pi * i / n
        dist = random.uniform(0.05, 0.15)
        lat = district["lat"] + dist * math.cos(angle)
        lon = district["lon"] + dist * math.sin(angle)
        name = random.choice(HABITATION_NAMES) + (f" {chr(65+i)}" if n > 1 else "")
        population = int(hab_pop * random.uniform(0.6, 1.4))
        area = round(population * random.uniform(0.0002, 0.0008), 4)

        flood = jitter(district["flood_risk"], 0.25)
        landslide = jitter(district.get("landslide_risk", 0.2), 0.25)
        seismic = jitter(random.uniform(0.3, 0.8), 0.2)
        erosion = jitter(district["flood_risk"] * 0.5, 0.25)

        combined_hazard = round(
            0.35 * flood + 0.25 * landslide + 0.25 * seismic + 0.15 * erosion, 2
        )

        poverty = round(random.uniform(0.1, 0.8), 2)
        age_vuln = round(random.uniform(0.1, 0.5), 2)
        disability = round(random.uniform(0.03, 0.25), 2)
        infra_quality = round(random.uniform(0.15, 0.9), 2)
        pop_density = round(population / max(area, 0.1), 1)

        combined_vuln = round(
            0.25 * poverty + 0.20 * age_vuln + 0.10 * disability + 0.45 * (1 - infra_quality), 2
        )

        exposure = round(random.uniform(0.1, 0.9), 2)

        overall_risk = round(0.4 * combined_hazard + 0.3 * combined_vuln + 0.3 * exposure, 2)

        if overall_risk >= 0.55:
            band = "immediate"
        elif overall_risk >= 0.42:
            band = "short_term"
        elif overall_risk >= 0.30:
            band = "medium_term"
        else:
            band = "monitor"

        habitations.append({
            "name": name,
            "district": district["name"],
            "lat": round(lat, 4),
            "lon": round(lon, 4),
            "population": population,
            "area_sq_km": area,
            "hazard": {
                "flood": flood,
                "landslide": landslide,
                "seismic": seismic,
                "erosion": erosion,
                "combined": combined_hazard,
                "confidence": round(random.uniform(0.7, 0.95), 2),
            },
            "vulnerability": {
                "population_density": pop_density,
                "poverty_index": poverty,
                "age_vulnerability": age_vuln,
                "disability_index": disability,
                "infrastructure_quality": infra_quality,
                "combined": combined_vuln,
            },
            "exposure": exposure,
            "risk": {
                "overall": overall_risk,
                "band": band,
                "confidence": round(random.uniform(0.65, 0.92), 2),
                "contributing_factors": {
                    "flood_risk": round(flood * 0.4, 3),
                    "seismic_risk": round(seismic * 0.25, 3),
                    "landslide_risk": round(landslide * 0.25, 3),
                    "vulnerability": round(combined_vuln * 0.3, 3),
                    "population_exposure": round(exposure * 0.3, 3),
                },
            },
        })
    return habitations


def gen_relocation_sites(habitation, n=3):
    sites = []
    for i in range(n):
        angle = 2 * math.pi * i / n
        dist = random.uniform(0.1, 0.3)
        lat = habitation["lat"] + dist * math.cos(angle)
        lon = habitation["lon"] + dist * math.sin(angle)

        max_cap = int(habitation["population"] * random.uniform(1.5, 4.0))
        water = round(random.uniform(0.5, 1.0), 2)
        health = round(random.uniform(0.4, 1.0), 2)
        school = round(random.uniform(0.5, 1.0), 2)
        road = round(random.uniform(0.5, 1.0), 2)
        env = round(random.uniform(0.6, 1.0), 2)
        livelihood = round(random.uniform(0.5, 1.0), 2)

        safety = round(1 - habitation["risk"]["overall"] + random.uniform(-0.1, 0.2), 2)
        capacity = round(min(max_cap / habitation["population"], 1.0), 2)
        accessibility = round((road + health + school) / 3, 2)

        suitability = round(
            0.30 * safety + 0.20 * capacity + 0.15 * accessibility +
            0.15 * (health + school) / 2 + 0.10 * env + 0.10 * livelihood, 2
        )

        verdict = "sufficient" if max_cap >= habitation["population"] else "insufficient"

        sites.append({
            "name": f"{habitation['name']} Site {chr(65+i)}",
            "habitation": habitation["name"],
            "lat": round(lat, 4),
            "lon": round(lon, 4),
            "area_sq_km": round(random.uniform(2, 15), 2),
            "existing_population": int(random.uniform(500, 3000)),
            "max_capacity": max_cap,
            "scores": {
                "safety": safety,
                "capacity": capacity,
                "accessibility": accessibility,
                "healthcare": health,
                "school": school,
                "road": road,
                "environment": env,
                "livelihood": livelihood,
            },
            "suitability_score": suitability,
            "carrying_capacity": {
                "verdict": verdict,
                "incoming_population": habitation["population"],
                "site_capacity": max_cap,
                "capacity_gap": max_cap - habitation["population"],
                "infrastructure_rating": round((health + school + road) / 3, 2),
                "water_availability": water,
            },
        })
    return sites


def generate():
    all_data = {"districts": [], "habitations": [], "relocation_sites": []}

    for dist in ASSAM_DISTRICTS:
        all_data["districts"].append({
            "name": dist["name"],
            "state": "Assam",
            "lat": dist["lat"],
            "lon": dist["lon"],
        })
        hab_count = random.randint(3, 6)
        habitations = gen_habitations(dist, hab_count)
        all_data["habitations"].extend(habitations)

        for hab in habitations:
            sites = gen_relocation_sites(hab, random.randint(2, 4))
            all_data["relocation_sites"].extend(sites)

    out = Path(__file__).parent / "assam_data.json"
    out.write_text(json.dumps(all_data, indent=2))
    print(f"Generated {len(all_data['districts'])} districts, "
          f"{len(all_data['habitations'])} habitations, "
          f"{len(all_data['relocation_sites'])} relocation sites")
    print(f"Saved to {out}")


if __name__ == "__main__":
    generate()
