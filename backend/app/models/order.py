from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    order_number: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(40), default="pending_payment")
    payment_status: Mapped[str] = mapped_column(String(40), default="initiated")
    payment_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2))
    customer_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))
    phone_number: Mapped[str] = mapped_column(String(32))
    alternate_phone_number: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    delivery_address: Mapped[str] = mapped_column(Text)
    pincode: Mapped[str] = mapped_column(String(16), default="")
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    coupon_code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    product_name: Mapped[str] = mapped_column(String(255))
    flavour: Mapped[str] = mapped_column(String(255))
    variant_label: Mapped[str] = mapped_column(String(32))
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2))
    quantity: Mapped[int] = mapped_column()
    line_total: Mapped[float] = mapped_column(Numeric(10, 2))

    order: Mapped["Order"] = relationship(back_populates="items")
