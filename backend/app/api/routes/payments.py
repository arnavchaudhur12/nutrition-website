from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.order import (
    RazorpayFailureRequest,
    RazorpayOrderCreateRequest,
    RazorpayOrderRead,
    RazorpayVerifyRead,
    RazorpayVerifyRequest,
)
from app.services.order_service import OrderService

router = APIRouter()


@router.post("/create-order", response_model=RazorpayOrderRead)
def create_razorpay_order(
    payload: RazorpayOrderCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    return OrderService(db).create_razorpay_order(payload, current_user)


@router.post("/verify-payment", response_model=RazorpayVerifyRead)
def verify_razorpay_payment(
    payload: RazorpayVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    return OrderService(db).verify_razorpay_payment(payload, current_user)


@router.post("/payment-failed", response_model=RazorpayVerifyRead)
def mark_razorpay_payment_failed(
    payload: RazorpayFailureRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    return OrderService(db).mark_razorpay_payment_failed(payload, current_user)
