"""Backend tests."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "SafeHabitat" in resp.json()["message"]


def test_state_summary():
    resp = client.get("/api/state/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "state" in data
    assert "band_counts" in data


def test_districts():
    resp = client.get("/api/districts")
    assert resp.status_code == 200
    districts = resp.json()
    assert len(districts) > 0
    assert "name" in districts[0]


def test_habitations():
    resp = client.get("/api/habitations?limit=10")
    assert resp.status_code == 200
    habitations = resp.json()
    assert len(habitations) <= 10


def test_relocation_sites():
    resp = client.get("/api/habitations/1/relocation")
    assert resp.status_code == 200
    sites = resp.json()
    assert isinstance(sites, list)


def test_nrsc_data():
    resp = client.get("/api/data/nrsc")
    assert resp.status_code == 200
    data = resp.json()
    assert "metadata" in data
    assert "satellite_datasets" in data["metadata"]


def test_data_sources():
    resp = client.get("/api/data/sources")
    assert resp.status_code == 200
    data = resp.json()
    assert "flood_hazard" in data
    assert "methodology" in data


def test_models_info():
    resp = client.get("/api/models/info")
    assert resp.status_code == 200
    data = resp.json()
    assert "models_trained" in data
