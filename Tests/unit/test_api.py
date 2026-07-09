from __future__ import annotations

from fastapi import status
from fastapi.testclient import TestClient

from API.main import app

client = TestClient(app)


class TestHealth:
    def test_health_check(self):
        response = client.get("/api/v1/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.1.0"
        assert data["uptime_seconds"] >= 0

    def test_health_method_not_allowed(self):
        response = client.post("/api/v1/health")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


class TestSources:
    def test_list_sources(self):
        response = client.get("/api/v1/sources")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "sources" in data
        assert isinstance(data["sources"], list)

    def test_get_source_not_found(self):
        response = client.get("/api/v1/sources/nonexistent")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]


class TestETL:
    def test_run_etl_not_implemented(self):
        response = client.post("/api/v1/etl/run", json={"source_id": "test", "mode": "full"})
        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED

    def test_run_etl_invalid_mode(self):
        response = client.post("/api/v1/etl/run", json={"source_id": "test", "mode": "invalid"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_etl_status_not_found(self):
        response = client.get("/api/v1/etl/runs/nonexistent")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestTrust:
    def test_trust_score_not_implemented(self):
        response = client.get("/api/v1/trust/score/test-source")
        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED

    def test_reconciliation_not_implemented(self):
        response = client.get("/api/v1/trust/reconciliation/a/b")
        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED


class TestDecisions:
    def test_circuit_breaker_state_not_implemented(self):
        response = client.get("/api/v1/decisions/circuit-breaker/test-source")
        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED

    def test_circuit_breaker_action_not_implemented(self):
        response = client.post(
            "/api/v1/decisions/circuit-breaker/test-source",
            json={"source_id": "test-source", "action": "reset"},
        )
        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED


class TestData:
    def test_query_not_implemented(self):
        response = client.post(
            "/api/v1/data/query",
            json={"source_id": "test", "layer": "gold", "limit": 10, "offset": 0},
        )
        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED

    def test_query_invalid_layer(self):
        response = client.post(
            "/api/v1/data/query",
            json={"source_id": "test", "layer": "invalid", "limit": 10, "offset": 0},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
