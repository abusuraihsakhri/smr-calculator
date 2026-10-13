"""HTTP and audit integrity regressions."""
import copy

from fastapi.testclient import TestClient
from agents.api import app
from agents.base import AuditTrail

client = TestClient(app)


def test_browser_page_is_served():
    response = client.get("/")
    assert response.status_code == 200
    assert "Standardized Mortality Ratio" in response.text
    assert client.get("/smr.js").status_code == 200
    assert client.get("/app.js").status_code == 200


def test_smr_endpoint():
    response = client.post("/api/smr", json={"observed": 10, "expected": 8})
    assert response.status_code == 200
    payload = response.json()
    assert payload["smr"] == 1.25
    assert payload["ci_lower"] < 1 < payload["ci_upper"]


def test_smr_bad_input():
    for data in [
        {"observed": -1, "expected": 4},
        {"observed": 1.25, "expected": 4},
        {"observed": 2, "expected": 0},
        {"observed": 2, "expected": 4, "confidence_level": 1},
    ]:
        assert client.post("/api/smr", json=data).status_code == 422


def test_audit_signature_catches_mutated_entry():
    ledger = AuditTrail(secret_key="test-only")
    ledger.log("tester", "test", "CALC", {"observed": 2})
    assert ledger.verify_integrity()
    external = ledger.get_trail()
    external[0]["event_type"] = "FORGED"
    assert ledger.verify_integrity()  # Defensive copy prevents external mutation.
    ledger.logs[0]["event_type"] = "FORGED"
    assert not ledger.verify_integrity()
