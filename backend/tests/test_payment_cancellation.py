import pytest
from sqlalchemy import create_engine, update
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models.order import Order
from app.schemas.order import RazorpayFailureRequest
from app.services.order_service import OrderService


@pytest.fixture
def checkout(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'checkout.db'}")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        order = Order(
            order_number="PENDING-TEST", payment_reference="order_cancel_test",
            total_amount=100, customer_name="Test Buyer", email="buyer@example.com",
            phone_number="9999999999", delivery_address="Test address",
        )
        db.add(order)
        db.commit()
        service = OrderService(db)
        failures = []
        monkeypatch.setattr(service.email_service, "send_payment_failure", lambda **kw: failures.append(kw))
        monkeypatch.setattr(service.payment_service, "get_captured_payment_id_for_order", lambda _: None)
        yield service, order, failures
    engine.dispose()


def cancellation():
    return RazorpayFailureRequest(
        razorpay_order_id="order_cancel_test", reason="cancelled",
        description="Customer closed the payment window before completing payment.",
    )


def test_cancellation_sends_failure_once_for_repeated_events(checkout):
    service, order, failures = checkout
    service.mark_razorpay_payment_failed(cancellation(), None)
    service.mark_razorpay_payment_failed(cancellation(), None)
    assert order.payment_status == "failed"
    assert len(failures) == 1
    assert failures[0]["buyer_email"] == "buyer@example.com"
    assert "Customer closed the payment window" in failures[0]["html_body"]


def test_cancellation_never_downgrades_paid_order(checkout, monkeypatch):
    service, order, failures = checkout
    order.payment_status = "paid"
    order.status = "confirmed"
    service.db.commit()

    def unexpected_lookup(_):
        pytest.fail("A paid order must not depend on a gateway lookup")

    monkeypatch.setattr(service.payment_service, "get_captured_payment_id_for_order", unexpected_lookup)
    service.mark_razorpay_payment_failed(cancellation(), None)
    assert order.payment_status == "paid"
    assert order.status == "confirmed"
    assert failures == []


@pytest.mark.parametrize("competing_status", ["paid", "failed"])
def test_stale_cancellation_cannot_overwrite_another_transition(checkout, monkeypatch, competing_status):
    service, order, failures = checkout

    def concurrent_transition(_):
        # Simulate a callback updating the database after this request's read.
        service.db.execute(
            update(Order).where(Order.id == order.id)
            .values(payment_status=competing_status)
            .execution_options(synchronize_session=False)
        )
        service.db.commit()
        return None

    monkeypatch.setattr(service.payment_service, "get_captured_payment_id_for_order", concurrent_transition)
    service.mark_razorpay_payment_failed(cancellation(), None)
    assert order.payment_status == competing_status
    assert failures == []


def test_cancellation_recovers_gateway_capture_instead_of_sending_failure(checkout, monkeypatch):
    service, order, failures = checkout
    confirmations = []
    monkeypatch.setattr(service.payment_service, "get_captured_payment_id_for_order", lambda _: "pay_captured")
    monkeypatch.setattr(service, "_mark_order_paid", lambda *args, **kw: confirmations.append(kw))
    service.mark_razorpay_payment_failed(cancellation(), None)
    assert confirmations == [{"razorpay_order_id": "order_cancel_test", "should_send_confirmation": True}]
    assert failures == []
