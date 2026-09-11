import csv
import io
import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "assam"
COMPLAINTS_FILE = Path(__file__).parent.parent.parent / "data" / "complaints.json"
_data = None


def load_data():
    global _data
    if _data is None:
        fp = DATA_DIR / "assam_data.json"
        if not fp.exists():
            raise HTTPException(500, "Data not generated.")
        _data = json.loads(fp.read_text())
    return _data


def csv_response(rows: list[dict], filename: str):
    if not rows:
        raise HTTPException(404, "No data found")
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/reports/state", tags=["Reports"])
def report_state():
    data = load_data()
    rows = []
    for d in data["districts"]:
        habs = [h for h in data["habitations"] if h["district"] == d["name"]]
        rows.append(
            {
                "district": d["name"],
                "total_habitations": len(habs),
                "population": sum(h["population"] for h in habs),
                "high_risk_count": len([h for h in habs if h["risk"]["band"] == "immediate"]),
                "avg_risk_score": round(
                    sum(h["risk"]["overall"] for h in habs) / max(len(habs), 1), 3
                ),
            }
        )
    return csv_response(rows, "state_overview.csv")


@router.get("/reports/district/{name}", tags=["Reports"])
def report_district(name: str):
    data = load_data()
    for d in data["districts"]:
        if d["name"].lower() == name.lower():
            habs = [h for h in data["habitations"] if h["district"] == d["name"]]
            rows = []
            for h in sorted(habs, key=lambda x: x["risk"]["overall"], reverse=True):
                haz = h.get("hazard", {})
                vuln = h.get("vulnerability", {})
                rows.append(
                    {
                        "habitation": h["name"],
                        "population": h["population"],
                        "risk_score": h["risk"]["overall"],
                        "risk_band": h["risk"]["band"],
                        "flood": haz.get("flood", 0),
                        "landslide": haz.get("landslide", 0),
                        "seismic": haz.get("seismic", 0),
                        "erosion": haz.get("erosion", 0),
                        "vulnerability": vuln.get("combined", 0),
                        "exposure": h.get("exposure", 0),
                        "relocation_sites": len(
                            [s for s in data["relocation_sites"] if s["habitation"] == h["name"]]
                        ),
                    }
                )
            return csv_response(rows, f"district_{name.lower().replace(' ', '_')}.csv")
    raise HTTPException(404, f"District '{name}' not found")


@router.get("/reports/habitation/{name}", tags=["Reports"])
def report_habitation(name: str):
    data = load_data()
    for h in data["habitations"]:
        if h["name"].lower() == name.lower():
            haz = h.get("hazard", {})
            vuln = h.get("vulnerability", {})
            risk = h.get("risk", {})
            rows = [
                {"field": "Name", "value": h["name"]},
                {"field": "District", "value": h["district"]},
                {"field": "Population", "value": h["population"]},
                {"field": "Area (sq km)", "value": h.get("area_sq_km", 0)},
                {"field": "Latitude", "value": h["lat"]},
                {"field": "Longitude", "value": h["lon"]},
                {"field": "Risk Score", "value": risk.get("overall", 0)},
                {"field": "Risk Band", "value": risk.get("band", "")},
                {"field": "Confidence", "value": risk.get("confidence", 0)},
                {"field": "Flood Risk", "value": haz.get("flood", 0)},
                {"field": "Landslide Risk", "value": haz.get("landslide", 0)},
                {"field": "Seismic Risk", "value": haz.get("seismic", 0)},
                {"field": "Erosion Risk", "value": haz.get("erosion", 0)},
                {"field": "Hazard Combined", "value": haz.get("combined", 0)},
                {"field": "Vulnerability", "value": vuln.get("combined", 0)},
                {"field": "Exposure", "value": h.get("exposure", 0)},
                {"field": "DFSI", "value": h.get("dfsi", 0)},
                {"field": "Historical Floods", "value": h.get("historical_flood_events", 0)},
            ]
            return csv_response(rows, f"habitation_{name.lower().replace(' ', '_')}.csv")
    raise HTTPException(404, f"Habitation '{name}' not found")


@router.get("/reports/relocation/{habitation_name}", tags=["Reports"])
def report_relocation(habitation_name: str):
    data = load_data()
    hab = None
    for h in data["habitations"]:
        if h["name"].lower() == habitation_name.lower():
            hab = h
            break
    if not hab:
        raise HTTPException(404, f"Habitation '{habitation_name}' not found")

    from app.engines.relocation_engine import relocation_engine

    sites = [s for s in data["relocation_sites"] if s["habitation"] == hab["name"]]
    ranked = relocation_engine.rank_sites(hab, sites)

    rows = []
    for s in ranked:
        scores = s.get("scores", {})
        cap = s.get("carrying_capacity", {})
        rows.append(
            {
                "site": s["name"],
                "suitability_score": s.get("suitability_score", 0),
                "safety": scores.get("safety", 0),
                "capacity": scores.get("capacity", 0),
                "accessibility": scores.get("accessibility", 0),
                "healthcare": scores.get("healthcare", 0),
                "school": scores.get("school", 0),
                "road": scores.get("road", 0),
                "environment": scores.get("environment", 0),
                "livelihood": scores.get("livelihood", 0),
                "max_capacity": s.get("max_capacity", 0),
                "verdict": cap.get("verdict", ""),
                "capacity_gap": cap.get("capacity_gap", 0),
            }
        )
    return csv_response(rows, f"relocation_{habitation_name.lower().replace(' ', '_')}.csv")


class Complaint(BaseModel):
    reporter_name: str
    phone: str
    missing_person_name: str
    last_seen_date: str
    last_seen_location: str
    description: str = ""


@router.post("/complaints", tags=["Complaints"])
def file_complaint(complaint: Complaint):
    complaints = []
    if COMPLAINTS_FILE.exists():
        complaints = json.loads(COMPLAINTS_FILE.read_text())

    record = complaint.model_dump()
    record["id"] = len(complaints) + 1
    record["filed_at"] = datetime.now().isoformat()
    record["status"] = "pending"
    complaints.append(record)

    COMPLAINTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    COMPLAINTS_FILE.write_text(json.dumps(complaints, indent=2))
    return {
        "status": "filed",
        "complaint_id": record["id"],
        "message": "Complaint filed successfully",
    }


@router.get("/complaints", tags=["Complaints"])
def list_complaints():
    if not COMPLAINTS_FILE.exists():
        return []
    return json.loads(COMPLAINTS_FILE.read_text())
