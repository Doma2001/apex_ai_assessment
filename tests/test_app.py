import os

import pytest

from app.main import create_app


@pytest.fixture
def client(tmp_path):
    return create_app(str(tmp_path / "t.db")).test_client()


def test_health_ok(client):
    assert client.get("/health").status_code == 200


def test_health_has_version(client):
    assert "version" in client.get("/health").get_json()


def test_ready_ok(client):
    assert client.get("/ready").status_code == 200


def test_ready_fails_when_db_missing():
    c = create_app("/nonexistent/dir/x.db").test_client()
    assert c.get("/ready").status_code == 503


def test_create_op(client):
    r = client.post("/ops", json={"name": "restart pump"})
    assert r.status_code == 201


def test_list_contains_created(client):
    client.post("/ops", json={"name": "check valve"})
    assert client.get("/ops").get_json()[0]["name"] == "check valve"


def test_create_requires_name(client):
    assert client.post("/ops", json={}).status_code == 400


def test_metrics_exposed(client):
    client.get("/health")
    assert "apex_requests_total" in client.get("/metrics").get_data(as_text=True)


@pytest.mark.skipif(os.getenv("FORCE_FAIL") != "1", reason="demo-only failure")
def test_intentional_failure():
    assert False, "Intentional failure: CI must block deployment"
