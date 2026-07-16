from datetime import datetime
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

    def list_paid_orders_in_date_range(
        self,
        start_at: datetime,
        end_before: datetime,
    ) -> list[Order]:
        result = self.db.execute(
            select(Order)
            .where(
                Order.payment_status == "paid",
                Order.status != "cancelled",
                Order.created_at >= start_at,
                Order.created_at < end_before,
            )
            .options(selectinload(Order.items))
            .order_by(Order.created_at.asc(), Order.id.asc())
        )
        return list(result.scalars().all())

    def get_by_payment_reference(self, payment_reference: str) -> Optional[Order]:
        result = self.db.execute(
            select(Order)
            .where(Order.payment_reference == payment_reference)
            .options(selectinload(Order.items))
        )
        return result.scalar_one_or_none()

    def get_by_order_number(self, order_number: str) -> Optional[Order]:
        result = self.db.execute(
            select(Order)
            .where(Order.order_number == order_number)
            .options(selectinload(Order.items))
        )
        return result.scalar_one_or_none()

    def get_next_order_sequence(self, start_from: int) -> int:
        order_numbers = self.db.execute(
            select(Order.order_number, Order.id, Order.payment_status, Order.status)
        ).all()
        highest_ln_sequence = 0
        highest_fallback_sequence = max(start_from - 1, 0)

        for order_number, order_id, payment_status, order_status in order_numbers:
            is_successful = payment_status == "paid" and order_status != "cancelled"
            if is_successful and order_number and order_number.startswith("LN-"):
                suffix = order_number[3:]
                if suffix.isdigit():
                    highest_ln_sequence = max(highest_ln_sequence, int(suffix))
                    continue

            if is_successful and order_id is not None:
                highest_fallback_sequence = max(highest_fallback_sequence, int(order_id))

        base_sequence = highest_ln_sequence or highest_fallback_sequence
        return base_sequence + 1

    def aggregate_total_revenue(self) -> float:
        result = self.db.execute(select(func.coalesce(func.sum(Order.total_amount), 0)))
        return float(result.scalar_one())
