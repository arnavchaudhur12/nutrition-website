from fastapi.testclient import TestClient

from app.main import app


def test_visitor_count_tracks_connect_and_disconnect() -> None:
    client = TestClient(app)

    connect_response = client.post("/api/visitors/connect")
    assert connect_response.status_code == 200
    connect_body = connect_response.json()
    assert connect_body["active_visitors"] >= 1
    assert isinstance(connect_body["session_id"], str)

    snapshot_response = client.get("/api/visitors")
    assert snapshot_response.status_code == 200
    assert snapshot_response.json()["active_visitors"] >= 1

    disconnect_response = client.post(
        "/api/visitors/disconnect",
        json={"session_id": connect_body["session_id"]},
    )
    assert disconnect_response.status_code == 200
    assert disconnect_response.json()["active_visitors"] >= 0
