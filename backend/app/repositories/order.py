from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.order import Order


class OrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, order: Order) -> Order:
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order

    def list_orders(self) -> list[Order]:
        result = self.db.execute(
            select(Order).options(selectinload(Order.items)).order_by(Order.created_at.desc())
        )
        return list(result.scalars().all())

    def list_orders_by_email(self, email: str) -> list[Order]:
        result = self.db.execute(
            select(Order)
            .where(Order.email == email)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
        )
        return list(result.scalars().all())

    def get_by_payment_reference(self, payment_reference: str) -> Optional[Order]:
        result = self.db.execute(
            select(Order)
            .where(Order.payment_reference == payment_reference)
            .options(selectinload(Order.items))
        )
        return result.scalar_one_or_none()

    def aggregate_total_revenue(self) -> float:
        result = self.db.execute(select(func.coalesce(func.sum(Order.total_amount), 0)))
        return float(result.scalar_one())
