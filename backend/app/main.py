from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import api
from app.monitoring.metrics import router as metrics_router

app = FastAPI(
    title="SafeHabitat AI",
    description="AI-Powered Multi-Hazard Habitation Risk & Relocation Decision Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=[
        {
            "name": "State Overview",
            "description": "Assam-wide risk summary and statistics",
        },
        {
            "name": "Districts",
            "description": "District-level risk data and habitations",
        },
        {
            "name": "Habitations",
            "description": "Village-level risk assessment and relocation",
        },
        {
            "name": "Explainability",
            "description": "SHAP-based AI explanation for risk scores",
        },
        {
            "name": "Relocation",
            "description": "Site selection and carrying capacity analysis",
        },
        {
            "name": "Scenario",
            "description": "What-if simulation for rainfall changes",
        },
        {
            "name": "Data Sources",
            "description": "NRSC/ISRO satellite data and methodology",
        },
        {
            "name": "Models",
            "description": "ML model information and training status",
        },
        {
            "name": "Evacuation",
            "description": "Safe route planning from red zones to safe relocation sites",
        },
        {
            "name": "Monitoring",
            "description": "System health and metrics",
        },
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router, prefix="/api")
app.include_router(metrics_router, prefix="/metrics")


@app.get("/")
def root():
    return {"message": "SafeHabitat AI API", "version": "1.0.0"}
