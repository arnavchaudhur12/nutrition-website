from fastapi.testclient import TestClient

from app.main import app


def test_visitor_count_tracks_connect_and_disconnect() -> None:
    client = TestClient(app)

    initial_response = client.get("/api/visitors")
    assert initial_response.status_code == 200
    initial_total = initial_response.json()["total_visitors"]

    track_response = client.post("/api/visitors/track")
    assert track_response.status_code == 200
    assert track_response.json()["total_visitors"] == initial_total + 1

    latest_response = client.get("/api/visitors")
    assert latest_response.status_code == 200
    assert latest_response.json()["total_visitors"] == initial_total + 1
