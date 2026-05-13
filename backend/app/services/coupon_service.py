from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.coupon import CouponCode
from app.repositories.coupon import CouponRepository
from app.schemas.coupon import CouponCreateRequest


class CouponService:
    def __init__(self, db: Session):
        self.repository = CouponRepository(db)

    def list_codes(self) -> list[CouponCode]:
        return self.repository.list_codes()

    def create_code(self, payload: CouponCreateRequest) -> CouponCode:
        existing = self.repository.get_by_code(payload.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Coupon code already exists.",
            )
        coupon = CouponCode(
            code=payload.code,
            discount_percent=payload.discount_percent,
        )
        return self.repository.create(coupon)

    def delete_code(self, code: str) -> None:
        normalized = code.strip().upper()
        coupon = self.repository.get_by_code(normalized)
        if not coupon:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found.")
        self.repository.delete(coupon)

    def get_discount_percent(self, code: str) -> int:
        normalized = code.strip().upper()
        if len(normalized) != 6 or not normalized.isalnum():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Coupon code must be exactly 6 alphanumeric characters.",
            )
        coupon = self.repository.get_by_code(normalized)
        if not coupon:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid coupon code.",
            )
        return coupon.discount_percent

