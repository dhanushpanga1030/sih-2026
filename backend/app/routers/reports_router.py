import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel

router = APIRouter()

COMPLAINTS_FILE = Path(__file__).parent.parent.parent / "data" / "complaints.json"
COMPLAINTS_PHOTOS_DIR = Path(__file__).parent.parent.parent / "data" / "complaints"


class Complaint(BaseModel):
    reporter_name: str
    phone: str
    missing_person_name: str
    last_seen_date: str
    last_seen_location: str
    description: str = ""


@router.post("/complaints", tags=["Complaints"])
async def file_complaint(
    reporter_name: str,
    phone: str,
    missing_person_name: str,
    last_seen_date: str,
    last_seen_location: str,
    description: str = "",
    photo: UploadFile | None = File(None),
):
    complaints = []
    if COMPLAINTS_FILE.exists():
        complaints = json.loads(COMPLAINTS_FILE.read_text())

    record = {
        "reporter_name": reporter_name,
        "phone": phone,
        "missing_person_name": missing_person_name,
        "last_seen_date": last_seen_date,
        "last_seen_location": last_seen_location,
        "description": description,
        "id": len(complaints) + 1,
        "filed_at": datetime.now().isoformat(),
        "status": "pending",
        "photo": None,
    }

    if photo and photo.filename:
        COMPLAINTS_PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
        ext = Path(photo.filename).suffix or ".jpg"
        photo_name = f"complaint_{record['id']}{ext}"
        photo_path = COMPLAINTS_PHOTOS_DIR / photo_name
        content = await photo.read()
        photo_path.write_bytes(content)
        record["photo"] = photo_name

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
