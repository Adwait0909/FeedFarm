"""KML import endpoint: protected by X-Admin-Token, accurate counts, generic errors."""
import pytest
from fastapi.testclient import TestClient

import asgi


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("VET_IMPORT_TOKEN", "unit-test-token")
    with TestClient(asgi.application) as test_client:
        yield test_client


def test_import_requires_the_admin_token(client):
    assert client.post("/api/veterinary/import").status_code == 403
    assert client.post("/api/veterinary/import", headers={"X-Admin-Token": "wrong"}).status_code == 403


def test_import_is_disabled_when_no_token_is_configured(monkeypatch):
    monkeypatch.delenv("VET_IMPORT_TOKEN", raising=False)
    with TestClient(asgi.application) as client:
        assert client.post("/api/veterinary/import", headers={"X-Admin-Token": ""}).status_code == 403
        assert client.post("/api/veterinary/import", headers={"X-Admin-Token": "anything"}).status_code == 403


def test_reimport_counts_existing_records_as_skipped(client):
    first = client.post("/api/veterinary/import", headers={"X-Admin-Token": "unit-test-token"})
    assert first.status_code == 200
    body = client.post("/api/veterinary/import", headers={"X-Admin-Token": "unit-test-token"}).json()
    assert body["inserted"] == 0 and body["skipped"] == 2178 and body["total_parsed"] == 2178
    assert client.get("/api/veterinary/stats").status_code == 200


def test_import_failure_returns_a_generic_message(client, monkeypatch):
    import sys
    service = next(m for name, m in sys.modules.items() if name.endswith("services.veterinary_service") and hasattr(m, "import_kml_to_db"))

    async def boom(db):
        raise RuntimeError("secret internal detail: /etc/passwd")

    monkeypatch.setattr(service, "import_kml_to_db", boom)
    response = client.post("/api/veterinary/import", headers={"X-Admin-Token": "unit-test-token"})
    assert response.status_code == 500
    assert "secret" not in response.text and "passwd" not in response.text
