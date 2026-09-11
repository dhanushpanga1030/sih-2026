"""Prometheus Metrics for SafeHabitat AI.

Exposes /metrics endpoint for monitoring.
"""

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

router = APIRouter()

# Request metrics
REQUEST_COUNT = Counter(
    "safehabitat_requests_total",
    "Total API requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "safehabitat_request_latency_seconds",
    "Request latency in seconds",
    ["endpoint"],
)

# ML model metrics
MODEL_PREDICTIONS = Counter(
    "safehabitat_model_predictions_total",
    "Total model predictions",
    ["model_type", "habitation_band"],
)

MODEL_LATENCY = Histogram(
    "safehabitat_model_latency_seconds",
    "Model inference latency",
    ["model_type"],
)

MODEL_ACCURACY = Gauge(
    "safehabitat_model_accuracy",
    "Current model accuracy",
    ["model_type"],
)

# Data metrics
DATA_INGESTION_COUNT = Counter(
    "safehabitat_data_ingestion_total",
    "Total data ingestion operations",
    ["source", "status"],
)

DATA_FRESHNESS = Gauge(
    "safehabitat_data_freshness_hours",
    "Hours since last data update",
    ["source"],
)

# Alert metrics
ALERTS_FIRED = Counter(
    "safehabitat_alerts_fired_total",
    "Total alerts fired",
    ["alert_type", "severity"],
)

# Habitats metrics
HABITATIONS_MONITORED = Gauge(
    "safehabitat_habitations_monitored",
    "Total habitations being monitored",
    ["district"],
)

RISK_DISTRIBUTION = Gauge(
    "safehabitat_risk_distribution",
    "Distribution of habitations by risk band",
    ["band"],
)


@router.get("/")
def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@router.get("/health/detailed")
def detailed_health():
    """Detailed health check with metrics."""
    from sqlalchemy import text

    from app.database import engine

    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_ok = True
    except Exception:
        pass

    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "version": "1.0.0",
        "metrics": {
            "requests": REQUEST_COUNT._value.get(),
            "predictions": MODEL_PREDICTIONS._value.get(),
        },
    }
