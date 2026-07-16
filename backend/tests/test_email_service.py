from datetime import datetime

from app.models.order import Order, OrderItem
from app.services.email_service import EmailService
from app.services.order_service import OrderService


def test_order_confirmation_sends_separate_messages_with_invoice(monkeypatch) -> None:
    service = EmailService()
    service.settings.smtp_host = "smtp.gmail.com"
    service.settings.smtp_password = "app-password"
    service.settings.notification_email = "admin@example.com"
    service.settings.smtp_user = "customercare@example.com"

    delivered_messages = []

    def fake_deliver(message) -> None:
        delivered_messages.append(message)

    monkeypatch.setattr(service, "_deliver", fake_deliver)

    service.send_order_confirmation(
        buyer_email="buyer@example.com",
        subject="Order confirmation",
        html_body="<p>Hello buyer</p>",
        attachments=[("invoice-LN-TEST.pdf", b"%PDF-1.4 test", "application", "pdf")],
    )

    assert len(delivered_messages) == 3
    assert {message["To"] for message in delivered_messages} == {
        "buyer@example.com",
        "admin@example.com",
        "customercare@example.com",
    }

    for message in delivered_messages:
        attachments = list(message.iter_attachments())
        assert len(attachments) == 1
        assert attachments[0].get_filename() == "invoice-LN-TEST.pdf"


def test_invoice_pdf_contains_order_details() -> None:
    order = Order(
        order_number="LN-TEST1234",
        total_amount=2499.0,
        customer_name="Test Customer",
        email="buyer@example.com",
        phone_number="9999999999",
        delivery_address="Mumbai",
        created_at=datetime(2026, 5, 13, 12, 0, 0),
        items=[
            OrderItem(
                product_name="Protein",
                flavour="Chocolate",
                variant_label="1kg",
                unit_price=2499.0,
                quantity=1,
                line_total=2499.0,
            )
        ],
    )

    filename, content, maintype, subtype = OrderService.build_invoice_attachment(order)

    assert filename == "LN-TEST1234.pdf"
    assert maintype == "application"
    assert subtype == "pdf"
    assert content.startswith(b"%PDF-1.4")
    assert b"TAX INVOICE" in content
    assert b"LN-TEST1234" in content
    assert b"Protein - Chocolate \\(1kg\\)" in content


def test_invoice_statement_pdf_contains_multiple_invoice_numbers() -> None:
    first_order = Order(
        order_number="LN-TEST1001",
        total_amount=2499.0,
        customer_name="First Customer",
        email="first@example.com",
        phone_number="9999999999",
        delivery_address="Mumbai",
        pincode="400001",
        created_at=datetime(2026, 5, 13, 12, 0, 0),
        items=[
            OrderItem(
                product_name="Protein",
                flavour="Chocolate",
                variant_label="1kg",
                unit_price=2499.0,
                quantity=1,
                line_total=2499.0,
            )
        ],
    )
    second_order = Order(
        order_number="LN-TEST1002",
        total_amount=1299.0,
        customer_name="Second Customer",
        email="second@example.com",
        phone_number="8888888888",
        delivery_address="Pune",
        pincode="411001",
        created_at=datetime(2026, 5, 14, 12, 0, 0),
        items=[
            OrderItem(
                product_name="Protein",
                flavour="Mawa Malai",
                variant_label="500g",
                unit_price=1299.0,
                quantity=1,
                line_total=1299.0,
            )
        ],
    )

    filename, content, maintype, subtype = OrderService.build_invoice_statement_attachment(
        [first_order, second_order],
        datetime(2026, 5, 13).date(),
        datetime(2026, 5, 14).date(),
    )

    assert filename == "invoice-statement-2026-05-13_to_2026-05-14.pdf"
    assert maintype == "application"
    assert subtype == "pdf"
    assert content.startswith(b"%PDF-1.4")
    assert b"LN-TEST1001" in content
    assert b"LN-TEST1002" in content
    assert b"Protein - Chocolate \\(1kg\\)" in content
    assert b"Protein - Mawa Malai \\(500g\\)" in content
    assert b"/Count 2" in content
