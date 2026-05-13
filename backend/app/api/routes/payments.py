from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.order import (
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
) -> dict[str, object]:
    return OrderService(db).create_razorpay_order(payload)


@router.post("/verify-payment", response_model=RazorpayVerifyRead)
def verify_razorpay_payment(
    payload: RazorpayVerifyRequest,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return OrderService(db).verify_razorpay_payment(payload)
