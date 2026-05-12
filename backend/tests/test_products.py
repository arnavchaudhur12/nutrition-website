from fastapi.testclient import TestClient

from app.main import app


def test_list_products_returns_catalog() -> None:
    client = TestClient(app)
    response = client.get("/api/products")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) >= 1
    assert "slug" in body[0]
    assert "variants" in body[0]
