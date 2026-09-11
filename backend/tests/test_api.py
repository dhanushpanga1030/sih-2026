"""Backend tests."""

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
    assert "band_distribution" in data


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
    resp = client.get("/api/relocation/Maibong A")
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


# --- Auth tests ---


def test_login_success():
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["role"] == "admin"
    assert data["username"] == "admin"


def test_login_wrong_password():
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401


def test_login_unknown_user():
    resp = client.post("/api/auth/login", json={"username": "nobody", "password": "x"})
    assert resp.status_code == 401


def test_protected_endpoint_no_token():
    resp = client.post("/api/scenario", json={"rainfall_delta": 20})
    assert resp.status_code == 401


def test_protected_endpoint_with_token():
    login = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    token = login.json()["access_token"]
    resp = client.post(
        "/api/scenario",
        json={"rainfall_delta": 10},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert "results" in resp.json()


def test_protected_cache_invalidate_admin_only():
    login = client.post("/api/auth/login", json={"username": "analyst", "password": "analyst123"})
    token = login.json()["access_token"]
    resp = client.post(
        "/api/cache/invalidate",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_protected_cache_invalidate_admin():
    login = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    token = login.json()["access_token"]
    resp = client.post(
        "/api/cache/invalidate",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
