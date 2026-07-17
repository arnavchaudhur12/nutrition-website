from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
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
    city: Mapped[str] = mapped_column(String(120), default="")
    state: Mapped[str] = mapped_column(String(120), default="")
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    coupon_code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    shipment_provider: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    shipment_order_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    shipment_status: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    awb_number: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    shipment_courier: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    shipment_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shipment_label_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shipment_estimated_delivery: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    shipment_tracking_history: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shipment_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shipment_created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    shipment_last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    product_slug: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    variant_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    product_name: Mapped[str] = mapped_column(String(255))
    flavour: Mapped[str] = mapped_column(String(255))
    variant_label: Mapped[str] = mapped_column(String(32))
    mrp: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2))
    quantity: Mapped[int] = mapped_column()
    line_total: Mapped[float] = mapped_column(Numeric(10, 2))

    order: Mapped["Order"] = relationship(back_populates="items")
