from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.services.email_service import EmailService
from app.services.payment_service import PaymentService


def _create_paid_order(client: TestClient, token: str, email: str) -> str:
    product = client.get("/api/products").json()[0]
    variant = product["variants"][0]

    create_response = client.post(
        "/api/create-order",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "currency": "INR",
            "customer_name": "Invoice Admin Test",
            "email": email,
            "phone_number": "9999999999",
            "delivery_address": "Test address",
            "pincode": "411001",
            "items": [
                {
                    "product_slug": product["slug"],
                    "variant_id": variant["id"],
                    "quantity": 1,
                }
            ],
        },
    )
    assert create_response.status_code == 200

    verify_response = client.post(
        "/api/verify-payment",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "razorpay_order_id": create_response.json()["order_id"],
            "razorpay_payment_id": f"pay_{uuid4().hex[:8]}",
            "razorpay_signature": "sig_test",
        },
    )
    assert verify_response.status_code == 200
    return verify_response.json()["order_number"]


def test_admin_can_download_invoice_statement(monkeypatch) -> None:
    client = TestClient(app)

    monkeypatch.setattr(
        PaymentService,
        "create_razorpay_order",
        lambda self, amount_paise, currency, receipt: {
            "order_id": f"order_{uuid4().hex[:8]}",
            "amount": amount_paise,
            "currency": currency,
            "receipt": receipt,
        },
    )
    monkeypatch.setattr(
        PaymentService,
        "verify_razorpay_signature",
        lambda self, order_id, payment_id, signature: True,
    )
    monkeypatch.setattr(
        EmailService,
        "send_order_confirmation",
        lambda self, buyer_email, subject, html_body, attachments: None,
    )

    email = f"invoice-{uuid4().hex[:8]}@example.com"
    register_response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Invoice Admin Test",
            "email": email,
            "password": "Password123!",
            "phone_number": "9999999999",
        },
    )
    customer_token = register_response.json()["access_token"]

    _create_paid_order(client, customer_token, email)

    admin_login = client.post(
        "/api/auth/login",
        json={
            "email": "jai.lagad@lagadsnutrition.in",
            "password": "Xuv1997$",
        },
    )
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]

    response = client.get(
        "/api/admin/invoice-statement/download?start_date=2026-01-01&end_date=2026-12-31",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "invoice-statement-2026-01-01_to_2026-12-31.pdf" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF-1.4")


def test_invoice_statement_requires_matching_date_range(monkeypatch) -> None:
    client = TestClient(app)
    monkeypatch.setattr(
        PaymentService,
        "create_razorpay_order",
        lambda self, amount_paise, currency, receipt: {
            "order_id": f"order_{uuid4().hex[:8]}",
            "amount": amount_paise,
            "currency": currency,
            "receipt": receipt,
        },
    )
    monkeypatch.setattr(
        PaymentService,
        "verify_razorpay_signature",
        lambda self, order_id, payment_id, signature: True,
    )
    monkeypatch.setattr(
        EmailService,
        "send_order_confirmation",
        lambda self, buyer_email, subject, html_body, attachments: None,
    )

    admin_login = client.post(
        "/api/auth/login",
        json={
            "email": "jai.lagad@lagadsnutrition.in",
            "password": "Xuv1997$",
        },
    )
    admin_token = admin_login.json()["access_token"]

    response = client.get(
        "/api/admin/invoice-statement/download?start_date=2026-07-16&end_date=2026-07-15",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "End date must be on or after start date."
