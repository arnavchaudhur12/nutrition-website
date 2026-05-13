from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.order import Order, OrderItem
from app.models.user import User
from app.repositories.order import OrderRepository
from app.repositories.product import ProductRepository
from app.schemas.order import (
    OrderCreateRequest,
    RazorpayOrderCreateRequest,
    RazorpayVerifyRequest,
)
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
        order = self._build_order(payload)
        order = self.orders.create(order)
        payment = self.payment_service.create_checkout_reference(
            float(order.total_amount), order.order_number
        )
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

    def create_razorpay_order(self, payload: RazorpayOrderCreateRequest) -> dict[str, object]:
        app_order_number = None
        receipt = payload.receipt

        if payload.items:
            order_payload = OrderCreateRequest(
                customer_name=payload.customer_name or "",
                email=str(payload.email or ""),
                phone_number=payload.phone_number or "",
                alternate_phone_number=payload.alternate_phone_number,
                delivery_address=payload.delivery_address or "",
                comments=payload.comments,
                items=payload.items,
            )
            order = self._build_order(order_payload)
            app_order_number = order.order_number
            amount_paise = max(100, int(round(float(order.total_amount) * 100)))
            receipt = receipt or order.order_number
        else:
            amount_paise = payload.amount or 0
            receipt = receipt or f"LN-{uuid4().hex[:10].upper()}"
            order = None

        payment_order = self.payment_service.create_razorpay_order(
            amount_paise=amount_paise,
            currency=payload.currency,
            receipt=receipt,
        )

        if order:
            order.payment_reference = str(payment_order["order_id"])
            self.orders.create(order)

        return {
            **payment_order,
            "app_order_number": app_order_number,
        }

    def verify_razorpay_payment(self, payload: RazorpayVerifyRequest) -> dict[str, object]:
        if (
            not payload.razorpay_order_id
            or not payload.razorpay_payment_id
            or not payload.razorpay_signature
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment id, order id, and signature are required.",
            )

        is_valid = self.payment_service.verify_razorpay_signature(
            order_id=payload.razorpay_order_id,
            payment_id=payload.razorpay_payment_id,
            signature=payload.razorpay_signature,
        )

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment signature verification failed.",
            )

        order = self.orders.get_by_payment_reference(payload.razorpay_order_id)
        if not order:
            return {"success": True, "order_number": None}

        order.status = "confirmed"
        order.payment_status = "paid"
        order.payment_reference = payload.razorpay_order_id
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)

        self.email_service.send_order_confirmation(
            buyer_email=order.email,
            subject=f"Order confirmation for {order.order_number}",
            html_body=self._build_email_body(order),
        )

        return {"success": True, "order_number": order.order_number}

    def _build_order(self, payload: OrderCreateRequest) -> Order:
        total_amount = 0.0
        order_items: list[OrderItem] = []

        for item in payload.items:
            if item.quantity < 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Item quantity must be at least 1.",
                )

            product = self.products.get_by_slug(item.product_slug)
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product not found: {item.product_slug}",
                )

            variant = next(
                (variant for variant in product.variants if variant.id == item.variant_id),
                None,
            )
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
        return Order(
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

    def list_customer_orders(self, user: User) -> list[Order]:
        return self.orders.list_orders_by_email(user.email)

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
