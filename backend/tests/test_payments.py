from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.models.coupon import CouponCode
from app.main import app
from app.repositories.order import OrderRepository
from app.repositories.product import ProductRepository
from app.services.email_service import EmailService
from app.services.payment_service import PaymentService


def test_guest_can_create_payment_order_without_login(monkeypatch) -> None:
    client = TestClient(app)

    def fake_create_razorpay_order(
        self: PaymentService,
        amount_paise: int,
        currency: str,
        receipt: str,
    ) -> dict[str, object]:
        return {
            "order_id": "order_guest_test",
            "amount": amount_paise,
            "currency": currency,
            "receipt": receipt,
        }

    monkeypatch.setattr(PaymentService, "create_razorpay_order", fake_create_razorpay_order)

    response = client.post(
        "/api/create-order",
        json={"amount": 100, "currency": "INR", "receipt": "test-receipt"},
    )

    assert response.status_code == 200
    assert response.json()["order_id"] == "order_guest_test"


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

    assert response.status_code == 200
    assert response.json()["order_id"] == "order_test_123"
    assert response.json()["app_order_number"].startswith("LN-")
    assert int(response.json()["app_order_number"].split("-")[1]) >= 13


def test_order_numbers_stay_sequential(monkeypatch) -> None:
    client = TestClient(app)
    created_receipts: list[str] = []

    def fake_create_razorpay_order(
        self: PaymentService,
        amount_paise: int,
        currency: str,
        receipt: str,
    ) -> dict[str, object]:
        created_receipts.append(receipt)
        return {
            "order_id": f"order_seq_{len(created_receipts)}",
            "amount": amount_paise,
            "currency": currency,
            "receipt": receipt,
        }

    monkeypatch.setattr(PaymentService, "create_razorpay_order", fake_create_razorpay_order)

    email = f"sequence-{uuid4().hex[:8]}@example.com"
    register_response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Sequence Test",
            "email": email,
            "password": "Password123!",
            "phone_number": "9999999999",
        },
    )
    token = register_response.json()["access_token"]

    product = client.get("/api/products").json()[0]
    variant = product["variants"][0]
    base_payload = {
        "currency": "INR",
        "customer_name": "Sequence Test",
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
    }

    first = client.post("/api/create-order", headers={"Authorization": f"Bearer {token}"}, json=base_payload)
    second = client.post("/api/create-order", headers={"Authorization": f"Bearer {token}"}, json=base_payload)

    assert first.status_code == 200
    assert second.status_code == 200
    first_sequence = int(first.json()["app_order_number"].split("-")[1])
    second_sequence = int(second.json()["app_order_number"].split("-")[1])
    assert first_sequence >= 13
    assert second_sequence == first_sequence + 1


def test_coupon_code_applies_discount(monkeypatch) -> None:
    client = TestClient(app)
    captured_amounts: list[int] = []

    def fake_create_razorpay_order(
        self: PaymentService,
        amount_paise: int,
        currency: str,
        receipt: str,
    ) -> dict[str, object]:
        captured_amounts.append(amount_paise)
        return {
            "order_id": "order_coupon_test",
            "amount": amount_paise,
            "currency": currency,
            "receipt": receipt,
        }

    monkeypatch.setattr(PaymentService, "create_razorpay_order", fake_create_razorpay_order)

    coupon_code = f"S{uuid4().hex[:5]}".upper()
    with SessionLocal() as db:
        db.add(CouponCode(code=coupon_code, discount_percent=10))
        db.commit()

    email = f"coupon-{uuid4().hex[:8]}@example.com"
    register_response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Coupon Test",
            "email": email,
            "password": "Password123!",
            "phone_number": "9999999999",
        },
    )
    token = register_response.json()["access_token"]

    product = client.get("/api/products").json()[0]
    variant = product["variants"][0]
    response_without_coupon = client.post(
        "/api/create-order",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "currency": "INR",
            "customer_name": "Coupon Test",
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

    response_with_coupon = client.post(
        "/api/create-order",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "currency": "INR",
            "customer_name": "Coupon Test",
            "email": email,
            "phone_number": "9999999999",
            "delivery_address": "Test address",
            "pincode": "411001",
            "coupon_code": coupon_code,
            "items": [
                {
                    "product_slug": product["slug"],
                    "variant_id": variant["id"],
                    "quantity": 1,
                }
            ],
        },
    )

    assert response_without_coupon.status_code == 200
    assert response_with_coupon.status_code == 200
    assert len(captured_amounts) >= 2
    original_amount = captured_amounts[0]
    discounted_amount = captured_amounts[1]
    assert discounted_amount == int(round(original_amount * 0.9))


def test_invalid_coupon_code_returns_bad_request(monkeypatch) -> None:
    client = TestClient(app)

    def fake_create_razorpay_order(
        self: PaymentService,
        amount_paise: int,
        currency: str,
        receipt: str,
    ) -> dict[str, object]:
        return {
            "order_id": "order_invalid_coupon_test",
            "amount": amount_paise,
            "currency": currency,
            "receipt": receipt,
        }

    monkeypatch.setattr(PaymentService, "create_razorpay_order", fake_create_razorpay_order)

    email = f"coupon-invalid-{uuid4().hex[:8]}@example.com"
    register_response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Coupon Invalid Test",
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
            "customer_name": "Coupon Invalid Test",
            "email": email,
            "phone_number": "9999999999",
            "delivery_address": "Test address",
            "pincode": "411001",
            "coupon_code": "BAD999",
            "items": [
                {
                    "product_slug": product["slug"],
                    "variant_id": variant["id"],
                    "quantity": 1,
                }
            ],
        },
    )

    assert response.status_code == 400


def test_out_of_stock_product_cannot_start_payment(monkeypatch) -> None:
    client = TestClient(app)

    def fake_create_razorpay_order(
        self: PaymentService,
        amount_paise: int,
        currency: str,
        receipt: str,
    ) -> dict[str, object]:
        return {
            "order_id": "order_out_of_stock",
            "amount": amount_paise,
            "currency": currency,
            "receipt": receipt,
        }

    monkeypatch.setattr(PaymentService, "create_razorpay_order", fake_create_razorpay_order)

    email = f"outofstock-{uuid4().hex[:8]}@example.com"
    register_response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Stock Test",
            "email": email,
            "password": "Password123!",
            "phone_number": "9999999999",
        },
    )
    token = register_response.json()["access_token"]

    product = client.get("/api/products").json()[0]
    variant = product["variants"][0]
    original_stock = variant["stock_quantity"]
    with SessionLocal() as db:
        stored_product = ProductRepository(db).get_by_slug(product["slug"])
        assert stored_product is not None
        stored_variant = next(item for item in stored_product.variants if item.id == variant["id"])
        stored_variant.stock_quantity = 0
        db.add(stored_variant)
        db.commit()

    response = client.post(
        "/api/create-order",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "currency": "INR",
            "customer_name": "Stock Test",
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

    assert response.status_code == 400
    assert "out of stock" in response.json()["detail"].lower()

    with SessionLocal() as db:
        stored_product = ProductRepository(db).get_by_slug(product["slug"])
        assert stored_product is not None
        stored_variant = next(item for item in stored_product.variants if item.id == variant["id"])
        stored_variant.stock_quantity = original_stock
        db.add(stored_variant)
        db.commit()


def test_razorpay_webhook_confirms_paid_order_without_frontend_verify(monkeypatch) -> None:
    client = TestClient(app)
    sent_confirmations: list[str] = []
    razorpay_order_id = f"order_webhook_{uuid4().hex[:10]}"

    def fake_create_razorpay_order(
        self: PaymentService,
        amount_paise: int,
        currency: str,
        receipt: str,
    ) -> dict[str, object]:
        return {
            "order_id": razorpay_order_id,
            "amount": amount_paise,
            "currency": currency,
            "receipt": receipt,
        }

    def fake_verify_webhook_signature(
        self: PaymentService, payload_body: bytes, signature: str
    ) -> bool:
        return signature == "test-signature"

    def fake_send_order_confirmation(
        self: EmailService,
        buyer_email: str,
        subject: str,
        html_body: str,
        attachments: list[dict[str, object]],
    ) -> None:
        sent_confirmations.append(buyer_email)

    monkeypatch.setattr(PaymentService, "create_razorpay_order", fake_create_razorpay_order)
    monkeypatch.setattr(
        PaymentService,
        "verify_razorpay_webhook_signature",
        fake_verify_webhook_signature,
    )
    monkeypatch.setattr(
        EmailService,
        "send_order_confirmation",
        fake_send_order_confirmation,
    )

    email = f"webhook-{uuid4().hex[:8]}@example.com"
    register_response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Webhook Test",
            "email": email,
            "password": "Password123!",
            "phone_number": "9999999999",
        },
    )
    token = register_response.json()["access_token"]

    product = client.get("/api/products").json()[0]
    variant = product["variants"][0]
    create_response = client.post(
        "/api/create-order",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "currency": "INR",
            "customer_name": "Webhook Test",
            "email": email,
            "phone_number": "9999999999",
            "delivery_address": "Webhook address",
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
    order_number = create_response.json()["app_order_number"]

    webhook_response = client.post(
        "/api/payments/webhook",
        headers={"X-Razorpay-Signature": "test-signature"},
        json={
            "event": "payment.captured",
            "payload": {
                "payment": {
                        "entity": {
                            "id": "pay_webhook_test",
                            "order_id": razorpay_order_id,
                            "notes": {"order_number": order_number},
                        }
                    }
                },
        },
    )

    assert webhook_response.status_code == 200
    assert webhook_response.json()["processed"] is True
    assert webhook_response.json()["order_number"] == order_number

    with SessionLocal() as db:
        order = OrderRepository(db).get_by_order_number(order_number)
        assert order is not None
        assert order.status == "confirmed"
        assert order.payment_status == "paid"
        product_after_payment = ProductRepository(db).get_by_slug(product["slug"])
        assert product_after_payment is not None
        paid_variant = next(item for item in product_after_payment.variants if item.id == variant["id"])
        assert paid_variant.stock_quantity == variant["stock_quantity"] - 1

    assert sent_confirmations == [email]
