from fastapi.testclient import TestClient

from app.main import app


def test_get_hero_settings_returns_images_and_copy() -> None:
    client = TestClient(app)
    response = client.get("/api/hero")

    assert response.status_code == 200
    body = response.json()
    assert "headline" in body
    assert "image_urls" not in body
    assert isinstance(body["images"], list)
    assert len(body["images"]) >= 1
