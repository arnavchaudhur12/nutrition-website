from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.order import Order, OrderItem
from app.repositories.order import OrderRepository
from app.repositories.product import ProductRepository
from app.schemas.order import OrderCreateRequest
from app.services.email_service import EmailService
from app.services.payment_service import PaymentService


class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.orders = OrderRepository(db)
        self.products = ProductRepository(db)
        self.payment_service = PaymentService()
        self.email_service = EmailService()

    def create_order(self, payload: OrderCreateRequest) -> dict[str, object]:
        total_amount = 0.0
        order_items: list[OrderItem] = []

        for item in payload.items:
            product = self.products.get_by_slug(item.product_slug)
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product not found: {item.product_slug}",
                )

            variant = next((variant for variant in product.variants if variant.id == item.variant_id), None)
            if not variant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Variant not found for product: {item.product_slug}",
                )

            line_total = float(variant.selling_price) * item.quantity
            total_amount += line_total
            order_items.append(
                OrderItem(
                    product_name=product.name,
                    flavour=product.flavour,
                    variant_label=variant.weight_label,
                    unit_price=float(variant.selling_price),
                    quantity=item.quantity,
                    line_total=line_total,
                )
            )

        order_number = f"LN-{uuid4().hex[:10].upper()}"
        order = Order(
            order_number=order_number,
            total_amount=total_amount,
            customer_name=payload.customer_name,
            email=payload.email,
            phone_number=payload.phone_number,
            alternate_phone_number=payload.alternate_phone_number,
            delivery_address=payload.delivery_address,
            comments=payload.comments,
            items=order_items,
        )

        order = self.orders.create(order)
        payment = self.payment_service.create_checkout_reference(total_amount, order_number)
        order.payment_reference = str(payment["gateway_reference"])
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)

        self.email_service.send_order_confirmation(
            buyer_email=payload.email,
            subject=f"Order confirmation for {order.order_number}",
            html_body=self._build_email_body(order),
        )

        return {
            "order_number": order.order_number,
            "status": order.status,
            "payment_status": order.payment_status,
            "total_amount": float(order.total_amount),
            "payment": payment,
        }

    @staticmethod
    def _build_email_body(order: Order) -> str:
        rows = "".join(
            [
                (
                    f"<tr><td>{item.product_name} - {item.flavour}</td>"
                    f"<td>{item.variant_label}</td><td>{item.quantity}</td>"
                    f"<td>Rs. {float(item.line_total):.2f}</td></tr>"
                )
                for item in order.items
            ]
        )
        return (
            f"<h2>Namaste from Lagads Nutrition</h2>"
            f"<p>Your order <strong>{order.order_number}</strong> has been created.</p>"
            f"<table border='1' cellpadding='8' cellspacing='0'>"
            f"<thead><tr><th>Product</th><th>Variant</th><th>Qty</th><th>Total</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>"
            f"<p>Customer: {order.customer_name}<br/>"
            f"Email: {order.email}<br/>"
            f"Phone: {order.phone_number}<br/>"
            f"Address: {order.delivery_address}</p>"
        )

