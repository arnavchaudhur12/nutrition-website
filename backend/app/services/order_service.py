from uuid import uuid4
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.order import Order, OrderItem
from app.models.user import User
from app.repositories.order import OrderRepository
from app.repositories.product import ProductRepository
from app.schemas.order import (
    OrderCreateRequest,
    RazorpayFailureRequest,
    RazorpayOrderCreateRequest,
    RazorpayVerifyRequest,
)
from app.services.email_service import EmailService
from app.services.payment_service import PaymentService
from app.services.coupon_service import CouponService


class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.orders = OrderRepository(db)
        self.products = ProductRepository(db)
        self.payment_service = PaymentService()
        self.email_service = EmailService()
        self.coupon_service = CouponService(db)

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
            attachments=[self._build_invoice_attachment(order)],
        )

        return {
            "order_number": order.order_number,
            "status": order.status,
            "payment_status": order.payment_status,
            "total_amount": float(order.total_amount),
            "payment": payment,
        }

    def create_razorpay_order(
        self, payload: RazorpayOrderCreateRequest, current_user: User
    ) -> dict[str, object]:
        app_order_number = None
        receipt = payload.receipt

        if payload.items:
            if payload.email and str(payload.email).lower() != current_user.email.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Checkout email must match the logged-in account.",
                )

            order_payload = OrderCreateRequest(
                customer_name=payload.customer_name or current_user.full_name,
                email=current_user.email,
                phone_number=payload.phone_number or current_user.phone_number or "",
                alternate_phone_number=payload.alternate_phone_number,
                delivery_address=payload.delivery_address or "",
                comments=payload.comments,
                items=payload.items,
            )
            order = self._build_order(order_payload)
            app_order_number = order.order_number
            subtotal = float(order.total_amount)
            discount_percent = self._get_coupon_discount_percent(payload.coupon_code)
            discounted_total = self._apply_discount(subtotal, discount_percent)
            order.total_amount = discounted_total
            amount_paise = max(100, int(round(discounted_total * 100)))
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

    def _get_coupon_discount_percent(self, coupon_code: Optional[str] = None) -> int:
        if not coupon_code:
            return 0
        return self.coupon_service.get_discount_percent(coupon_code)

    @staticmethod
    def _apply_discount(amount: float, discount_percent: int) -> float:
        if discount_percent <= 0:
            return amount
        discount_amount = (amount * discount_percent) / 100
        return max(1.0, round(amount - discount_amount, 2))

    def verify_razorpay_payment(
        self, payload: RazorpayVerifyRequest, current_user: User
    ) -> dict[str, object]:
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
        self._ensure_order_owner(order, current_user)

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
            attachments=[self._build_invoice_attachment(order)],
        )

        return {"success": True, "order_number": order.order_number}

    def mark_razorpay_payment_failed(
        self, payload: RazorpayFailureRequest, current_user: User
    ) -> dict[str, object]:
        order = self.orders.get_by_payment_reference(payload.razorpay_order_id)
        if not order:
            return {"success": True, "order_number": None}
        self._ensure_order_owner(order, current_user)

        order.status = "payment_failed"
        order.payment_status = "failed"
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)

        failure_reason = payload.description or payload.reason or "Payment failed or was cancelled."
        self.email_service.send_payment_failure(
            buyer_email=order.email,
            subject=f"Payment failed for {order.order_number}",
            html_body=self._build_payment_failure_email_body(order, failure_reason),
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
    def _ensure_order_owner(order: Order, user: User) -> None:
        if order.email.lower() != user.email.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This payment does not belong to the logged-in account.",
            )

    @staticmethod
    def _build_email_body(order: Order) -> str:
        created_date = order.created_at.strftime("%d-%m-%Y") if order.created_at else ""
        subtotal = float(order.total_amount)
        rows = "".join(
            [
                (
                    f"<tr>"
                    f"<td style='padding:11px;border-bottom:1px solid #e6e7ef;'>{item.product_name}</td>"
                    f"<td style='padding:11px;border-bottom:1px solid #e6e7ef;'>{item.flavour}</td>"
                    f"<td style='padding:11px;border-bottom:1px solid #e6e7ef;text-align:center;'>{item.quantity}</td>"
                    f"<td style='padding:11px;border-bottom:1px solid #e6e7ef;text-align:right;'>Rs. {float(item.line_total):.2f}</td>"
                    f"</tr>"
                )
                for item in order.items
            ]
        )
        return (
            f"<div style='font-family:Arial,Helvetica,sans-serif;max-width:860px;margin:0 auto;color:#151515;"
            f"background:#ffffff;border:1px solid #ececf4;border-radius:14px;padding:24px;'>"
            f"<h1 style='margin:0 0 8px;font-size:34px;line-height:1.1;color:#222258;'>Tax Invoice</h1>"
            f"<div style='height:2px;background:#9088e6;margin:0 0 18px;'></div>"
            f"<table style='width:100%;border-collapse:collapse;margin-bottom:18px;'>"
            f"<tr>"
            f"<td style='vertical-align:top;padding-right:12px;'>"
            f"<h2 style='margin:0 0 8px;font-size:24px;color:#151515;'>Lagad's Nutrition</h2>"
            f"<p style='margin:0 0 6px;'>Phone no.: {order.phone_number}</p>"
            f"<p style='margin:0 0 6px;'>Email: customercare@lagadsnutrition.in</p>"
            f"<p style='margin:0;'>State: Dadra & Nagar Haveli & Daman & Diu</p>"
            f"</td>"
            f"<td style='vertical-align:top;text-align:right;'>"
            f"<p style='margin:0 0 6px;'><strong>Invoice No:</strong> {order.order_number}</p>"
            f"<p style='margin:0;'><strong>Date:</strong> {created_date}</p>"
            f"</td>"
            f"</tr>"
            f"</table>"
            f"<table style='width:100%;border-collapse:collapse;margin-bottom:16px;'>"
            f"<tr>"
            f"<td style='vertical-align:top;padding-right:12px;'>"
            f"<p style='margin:0 0 8px;font-size:20px;font-weight:700;color:#1f1f57;'>Bill To</p>"
            f"<p style='margin:0 0 6px;'><strong>{order.customer_name}</strong></p>"
            f"<p style='margin:0 0 6px;'>Contact No.: {order.phone_number}</p>"
            f"<p style='margin:0;'>Address: {order.delivery_address}</p>"
            f"</td>"
            f"<td style='vertical-align:top;text-align:right;'>"
            f"<p style='margin:0 0 8px;font-size:20px;font-weight:700;color:#1f1f57;'>Payment Status</p>"
            f"<p style='margin:0 0 6px;'>Paid via Razorpay</p>"
            f"<p style='margin:0;'>Email: {order.email}</p>"
            f"</td>"
            f"</tr>"
            f"</table>"
            f"<table style='width:100%;border-collapse:collapse;border:1px solid #e6e7ef;margin-top:8px;'>"
            f"<thead style='background:#8f87e4;color:#ffffff;'>"
            f"<tr><th style='padding:12px;text-align:left;'>Item Name</th>"
            f"<th style='padding:12px;text-align:left;'>Flavour</th>"
            f"<th style='padding:12px;text-align:center;'>Qty</th>"
            f"<th style='padding:12px;text-align:right;'>Amount</th></tr></thead>"
            f"<tbody>{rows}</tbody>"
            f"<tfoot>"
            f"<tr><td colspan='2' style='padding:12px;font-weight:700;'>Total</td>"
            f"<td style='padding:12px;text-align:center;font-weight:700;'>{sum(item.quantity for item in order.items)}</td>"
            f"<td style='padding:12px;text-align:right;font-weight:700;'>Rs. {subtotal:.2f}</td></tr>"
            f"</tfoot></table>"
            f"<table style='width:100%;border-collapse:collapse;margin-top:18px;'>"
            f"<tr>"
            f"<td style='vertical-align:top;padding-right:12px;'>"
            f"<p style='margin:0 0 8px;font-size:18px;font-weight:700;color:#1f1f57;'>Terms & Conditions</p>"
            f"<p style='margin:0;'>Thank you for doing business with us.</p>"
            f"</td>"
            f"<td style='vertical-align:top;text-align:right;min-width:260px;'>"
            f"<table style='width:100%;border-collapse:collapse;border:1px solid #e6e7ef;'>"
            f"<tr><td style='padding:10px;'>Sub Total</td>"
            f"<td style='padding:10px;text-align:right;'>Rs. {subtotal:.2f}</td></tr>"
            f"<tr style='background:#8f87e4;color:#fff;font-weight:700;'><td style='padding:10px;'>Total</td>"
            f"<td style='padding:10px;text-align:right;'>Rs. {subtotal:.2f}</td></tr>"
            f"</table>"
            f"</td>"
            f"</tr>"
            f"</table>"
            f"<p style='margin:22px 0 0;color:#4b5563;'>A PDF invoice is attached for your records.</p>"
            f"</div>"
        )

    @staticmethod
    def _build_payment_failure_email_body(order: Order, reason: str) -> str:
        return (
            f"<div style='font-family:Arial,sans-serif;max-width:720px;margin:0 auto;color:#111827;'>"
            f"<h2 style='margin-bottom:8px;'>Payment could not be completed</h2>"
            f"<p style='margin-top:0;'>Order <strong>{order.order_number}</strong> is marked as payment failed.</p>"
            f"<div style='background:#fef2f2;border:1px solid #fecaca;border-radius:12px;padding:16px;margin:20px 0;'>"
            f"<p style='margin:0 0 8px;'><strong>Reason:</strong> {reason}</p>"
            f"<p style='margin:0 0 8px;'><strong>Customer:</strong> {order.customer_name}</p>"
            f"<p style='margin:0 0 8px;'><strong>Email:</strong> {order.email}</p>"
            f"<p style='margin:0 0 8px;'><strong>Phone:</strong> {order.phone_number}</p>"
            f"<p style='margin:0;'><strong>Delivery Address:</strong> {order.delivery_address}</p>"
            f"</div>"
            f"<p>You can retry the payment from the website if needed.</p>"
            f"</div>"
        )

    @classmethod
    def _build_invoice_attachment(cls, order: Order) -> tuple[str, bytes, str, str]:
        filename = f"invoice-{order.order_number}.pdf"
        return (filename, cls._render_invoice_pdf(order), "application", "pdf")

    @classmethod
    def _render_invoice_pdf(cls, order: Order) -> bytes:
        lines = [
            "Lagads Nutrition Invoice",
            f"Invoice No: {order.order_number}",
            f"Date: {order.created_at.strftime('%d %b %Y %I:%M %p') if order.created_at else ''}",
            "",
            f"Customer: {order.customer_name}",
            f"Email: {order.email}",
            f"Phone: {order.phone_number}",
            f"Address: {order.delivery_address}",
            "",
            "Items:",
        ]

        for item in order.items:
            lines.append(
                f"- {item.product_name} | {item.flavour} | {item.variant_label} | "
                f"Qty {item.quantity} | Rs. {float(item.line_total):.2f}"
            )

        lines.extend(
            [
                "",
                f"Grand Total: Rs. {float(order.total_amount):.2f}",
                "",
                "Thank you for shopping with Lagads Nutrition.",
            ]
        )

        content_lines = ["BT", "/F1 12 Tf", "50 790 Td"]
        for index, line in enumerate(lines):
            if index:
                content_lines.append("0 -18 Td")
            content_lines.append(f"({cls._escape_pdf_text(line)}) Tj")
        content_lines.append("ET")

        content = "\n".join(content_lines).encode("latin-1", "replace")
        objects = [
            b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
            b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
            (
                b"3 0 obj\n"
                b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\n"
                b"endobj\n"
            ),
            b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
            (
                f"5 0 obj\n<< /Length {len(content)} >>\nstream\n".encode("ascii")
                + content
                + b"\nendstream\nendobj\n"
            ),
        ]

        pdf = bytearray(b"%PDF-1.4\n")
        offsets: list[int] = [0]
        for obj in objects:
            offsets.append(len(pdf))
            pdf.extend(obj)

        xref_offset = len(pdf)
        pdf.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
        pdf.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
        pdf.extend(
            (
                f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\n"
                f"startxref\n{xref_offset}\n%%EOF"
            ).encode("ascii")
        )
        return bytes(pdf)

    @staticmethod
    def _escape_pdf_text(value: str) -> str:
        return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
