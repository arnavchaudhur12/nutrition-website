from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.coupon import CouponCode


class CouponRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_codes(self) -> list[CouponCode]:
        result = self.db.execute(select(CouponCode).order_by(CouponCode.created_at.desc()))
        return list(result.scalars().all())

    def get_by_code(self, code: str) -> Optional[CouponCode]:
        result = self.db.execute(select(CouponCode).where(CouponCode.code == code))
        return result.scalar_one_or_none()

    def create(self, coupon: CouponCode) -> CouponCode:
        self.db.add(coupon)
        self.db.commit()
        self.db.refresh(coupon)
        return coupon

    def delete(self, coupon: CouponCode) -> None:
        self.db.delete(coupon)
        self.db.commit()
