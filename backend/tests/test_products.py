from fastapi.testclient import TestClient

from app.main import app
from app.schemas.product import ProductCreate


def test_list_products_returns_catalog() -> None:
    client = TestClient(app)
    response = client.get("/api/products")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) >= 1
    assert "slug" in body[0]
    assert "variants" in body[0]


def test_product_create_normalizes_admin_payload_placeholders() -> None:
    product = ProductCreate.model_validate(
        {
            "slug": "",
            "name": "Happy Raksha Bandhan Special Pack Combo",
            "flavour": "Mawa malai creamy 500g + dark chocolate crispy 500g",
            "description": "",
            "image_url": "/uploads/b7b915753f5949e2a258bf7768b41cfa.jpeg",
            "image_urls": ["/uploads/b7b915753f5949e2a258bf7768b41cfa.jpeg"],
            "category": "Peanut Butter",
            "variants": [
                {"weight_label": "1", "mrp": 768, "selling_price": 649, "stock_quantity": 100},
                {"weight_label": "500", "mrp": 0, "selling_price": 0, "stock_quantity": 100},
            ],
        }
    )

    assert product.slug == "happy-raksha-bandhan-special-pack-combo"
    assert product.description == "Happy Raksha Bandhan Special Pack Combo - Mawa malai creamy 500g + dark chocolate crispy 500g"
    assert len(product.variants) == 1
