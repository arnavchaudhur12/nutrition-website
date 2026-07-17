from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user_optional
from app.db.session import get_db
from app.models.user import User
from app.schemas.order import (
    RazorpayFailureRequest,
    RazorpayOrderCreateRequest,
    RazorpayOrderRead,
    RazorpayVerifyRead,
    RazorpayVerifyRequest,
    ServiceabilityRead,
)
from app.services.order_service import OrderService
from app.services.payment_service import PaymentService

router = APIRouter()


@router.post("/create-order", response_model=RazorpayOrderRead)
def create_razorpay_order(
    payload: RazorpayOrderCreateRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> dict[str, object]:
    return OrderService(db).create_razorpay_order(payload, current_user)


@router.post("/verify-payment", response_model=RazorpayVerifyRead)
def verify_razorpay_payment(
    payload: RazorpayVerifyRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> dict[str, object]:
    return OrderService(db).verify_razorpay_payment(payload, current_user)


@router.post("/payment-failed", response_model=RazorpayVerifyRead)
def mark_razorpay_payment_failed(
    payload: RazorpayFailureRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> dict[str, object]:
    return OrderService(db).mark_razorpay_payment_failed(payload, current_user)


@router.get("/coupon-preview")
def preview_coupon_discount(
    code: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> dict[str, object]:
    _ = current_user
    discount_percent = OrderService(db).coupon_service.get_discount_percent(code)
    return {"code": code.strip().upper(), "discount_percent": discount_percent}


@router.get("/serviceability", response_model=ServiceabilityRead)
def check_delivery_serviceability(
    delivery_pincode: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> dict[str, object]:
    _ = current_user
    _ = db
    return OrderService(db).check_delivery_serviceability(delivery_pincode)


@router.post("/payments/webhook")
async def handle_razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_razorpay_signature: str = Header(default="", alias="X-Razorpay-Signature"),
) -> dict[str, object]:
    if not x_razorpay_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Razorpay webhook signature.",
        )

    body = await request.body()
    if not PaymentService().verify_razorpay_webhook_signature(body, x_razorpay_signature):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Razorpay webhook signature.",
        )

    payload: dict[str, Any] = await request.json()
    event_type = str(payload.get("event") or "").strip()
    if not event_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Razorpay event type.",
        )

    return OrderService(db).handle_razorpay_webhook(event_type, payload)
