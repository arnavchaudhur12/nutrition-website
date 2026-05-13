from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.services.payment_service import PaymentService


def test_create_payment_order_requires_login() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/create-order",
        json={"amount": 100, "currency": "INR", "receipt": "test-receipt"},
    )

    assert response.status_code == 401


def test_logged_in_customer_can_create_payment_order(monkeypatch) -> None:
    client = TestClient(app)

    def fake_create_razorpay_order(
        self: PaymentService,
        amount_paise: int,
        currency: str,
        receipt: str,
    ) -> dict[str, object]:
        return {
            "order_id": "order_test_123",
            "amount": amount_paise,
            "currency": currency,
            "receipt": receipt,
        }

    monkeypatch.setattr(PaymentService, "create_razorpay_order", fake_create_razorpay_order)

    email = f"payment-{uuid4().hex[:8]}@example.com"
    register_response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Payment Test",
            "email": email,
            "password": "Password123!",
            "phone_number": "9999999999",
        },
    )
    token = register_response.json()["access_token"]

    product = client.get("/api/products").json()[0]
    variant = product["variants"][0]
    response = client.post(
        "/api/create-order",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "currency": "INR",
            "customer_name": "Payment Test",
            "email": email,
            "phone_number": "9999999999",
            "delivery_address": "Test address",
            "items": [
                {
                    "product_slug": product["slug"],
                    "variant_id": variant["id"],
                    "quantity": 1,
                }
            ],
        },
    )

    assert response.status_code == 200
    assert response.json()["order_id"] == "order_test_123"
