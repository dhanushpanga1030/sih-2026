"""Celery configuration for background tasks."""

import os

from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

app = Celery("safehabitat", broker=REDIS_URL, backend=REDIS_URL)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


@app.task(bind=True, name="ingest_district")
def ingest_district_task(self, district_name: str, bbox: dict):
    """Background task for data ingestion."""
    from app.ingestion.real_data_pipeline import pipeline

    result = pipeline.ingest_district(district_name, bbox)
    return result


@app.task(bind=True, name="retrain_models")
def retrain_models_task(self):
    """Background task for model retraining."""
    import subprocess

    result = subprocess.run(["python", "-m", "app.ml.train"], capture_output=True, text=True)
    return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}


@app.task(bind=True, name="batch_risk_assessment")
def batch_risk_assessment_task(self, district_id: int):
    """Background task for batch risk assessment."""
    from app.database import SessionLocal
    from app.engines.hazard_engine import HazardEngine
    from app.engines.risk_engine import RiskEngine
    from app.models.spatial_models import Habitation

    hazard_engine = HazardEngine()
    risk_engine = RiskEngine()

    db = SessionLocal()
    try:
        habitations = db.query(Habitation).filter(Habitation.district_id == district_id).all()
        results = []
        for hab in habitations:
            hazard_scores = {
                "flood": hab.hazard_scores.flood_score if hab.hazard_scores else 0.5,
                "landslide": hab.hazard_scores.landslide_score if hab.hazard_scores else 0.5,
                "seismic": hab.hazard_scores.seismic_score if hab.hazard_scores else 0.5,
            }
            scores = hazard_engine.combine_hazard(hazard_scores)
            results.append({"habitation": hab.name, "scores": scores})
        return {"processed": len(results), "results": results}
    finally:
        db.close()


@app.task(name="monitor_drift")
def monitor_drift_task():
    """Scheduled task to check for data drift."""
    from app.monitoring.drift_monitor import monitor

    # Run drift checks
    return {"alerts": monitor.get_alerts()}
