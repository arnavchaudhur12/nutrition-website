import json
from datetime import date, datetime, time, timedelta
from typing import Optional
from uuid import uuid4
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.order import Order, OrderItem
from app.models.user import User
from app.repositories.order import OrderRepository
from app.repositories.product import ProductRepository
from app.schemas.order import (
    AdminCouponOrderSummaryRead,
    AdminCustomerPortfolioRead,
    CustomerOrderRead,
    CustomerOrderShipmentRead,
    OrderCreateRequest,
    RazorpayFailureRequest,
    RazorpayOrderCreateRequest,
    RazorpayVerifyRequest,
    ShipmentTrackingEventRead,
)
from app.services.email_service import EmailService
from app.services.google_sheet_service import GoogleSheetService
from app.services.payment_service import PaymentService
from app.services.coupon_service import CouponService
from app.services.shipping_service import ShippingService


class OrderService:
    GST_RATE = 0.05
    FIXED_HSN_CODE = "21069099"

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.orders = OrderRepository(db)
        self.products = ProductRepository(db)
        self.payment_service = PaymentService()
        self.email_service = EmailService()
        self.coupon_service = CouponService(db)
        self.shipping_service = ShippingService()

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
            attachments=[self.build_invoice_attachment(order)],
        )

        return {
            "order_number": order.order_number,
            "status": order.status,
            "payment_status": order.payment_status,
            "total_amount": float(order.total_amount),
            "payment": payment,
        }

    def create_razorpay_order(
        self, payload: RazorpayOrderCreateRequest, current_user: Optional[User]
    ) -> dict[str, object]:
        app_order_number = None
        receipt = payload.receipt

        if payload.items:
            self._ensure_delivery_serviceable(payload.pincode or "")
            if current_user and payload.email and str(payload.email).lower() != current_user.email.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Checkout email must match the logged-in account.",
                )

            order_payload = OrderCreateRequest(
                customer_name=payload.customer_name or (current_user.full_name if current_user else ""),
                email=current_user.email if current_user else payload.email,  # type: ignore[arg-type]
                phone_number=payload.phone_number or (current_user.phone_number if current_user else "") or "",
                alternate_phone_number=payload.alternate_phone_number or "",
                delivery_address=payload.delivery_address or "",
                pincode=payload.pincode or "",
                city=payload.city or "",
                state=payload.state or "",
                comments=payload.comments or "",
                items=payload.items,
            )
            order = self._build_order(
                order_payload,
                order_number=self._generate_pending_order_number(),
            )
            app_order_number = order.order_number
            subtotal = float(order.total_amount)
            discount_percent = self._get_coupon_discount_percent(payload.coupon_code)
            discounted_total = self._apply_discount(subtotal, discount_percent)
            order.total_amount = discounted_total
            order.coupon_code = payload.coupon_code.strip().upper() if payload.coupon_code else None
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

    def check_delivery_serviceability(self, delivery_pincode: str) -> dict[str, object]:
        data = self._ensure_delivery_serviceable(delivery_pincode)
        return {
            "is_serviceable": bool(data.get("is_serviceable")),
            "pickup_pincode": str(data.get("pickup_pincode") or ""),
            "delivery_pincode": str(data.get("delivery_pincode") or delivery_pincode.strip()),
            "estimated_delivery_days": self._int_or_none(data.get("estimated_delivery_days")),
            "cod_available": self._bool_or_none(data.get("cod_available")),
            "available_couriers": [
                str(item).strip()
                for item in data.get("available_couriers", [])
                if str(item).strip()
            ] if isinstance(data.get("available_couriers"), list) else [],
            "min_rate": self._float_or_none(data.get("min_rate")),
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
        self, payload: RazorpayVerifyRequest, current_user: Optional[User]
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
        if current_user:
            self._ensure_order_owner(order, current_user)

        self._mark_order_paid(
            order,
            razorpay_order_id=payload.razorpay_order_id,
            should_send_confirmation=order.payment_status != "paid",
        )

        return {"success": True, "order_number": order.order_number}

    def mark_razorpay_payment_failed(
        self, payload: RazorpayFailureRequest, current_user: Optional[User]
    ) -> dict[str, object]:
        order = self.orders.get_by_payment_reference(payload.razorpay_order_id)
        if not order:
            return {"success": True, "order_number": None}
        if current_user:
            self._ensure_order_owner(order, current_user)

        order.status = "payment_failed"
        order.payment_status = "failed"
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)

        failure_reason = payload.description or payload.reason or "Payment failed or was cancelled."
        self.email_service.send_payment_failure(
            buyer_email=order.email,
            subject=self._build_payment_failure_subject(order),
            html_body=self._build_payment_failure_email_body(order, failure_reason),
        )

        return {"success": True, "order_number": order.order_number}

    def handle_razorpay_webhook(self, event_type: str, payload: dict[str, Any]) -> dict[str, object]:
        if event_type not in {"payment.captured", "order.paid"}:
            return {"success": True, "processed": False}

        payment_entity = self._extract_entity(payload, "payment")
        order_entity = self._extract_entity(payload, "order")
        order = self._find_order_for_razorpay_payload(payment_entity, order_entity)
        if not order:
            return {"success": True, "processed": False}

        already_paid = order.payment_status == "paid"
        razorpay_order_id = str(
            payment_entity.get("order_id")
            or order_entity.get("id")
            or order.payment_reference
            or ""
        )
        self._mark_order_paid(
            order,
            razorpay_order_id=razorpay_order_id,
            should_send_confirmation=not already_paid,
        )
        return {"success": True, "processed": True, "order_number": order.order_number}

    @staticmethod
    def _extract_entity(payload: dict[str, Any], entity_name: str) -> dict[str, Any]:
        raw_entity = payload.get("payload", {}).get(entity_name, {}).get("entity", {})
        return raw_entity if isinstance(raw_entity, dict) else {}

    def _find_order_for_razorpay_payload(
        self, payment_entity: dict[str, Any], order_entity: dict[str, Any]
    ) -> Optional[Order]:
        order_id = str(payment_entity.get("order_id") or order_entity.get("id") or "").strip()
        if order_id:
            order = self.orders.get_by_payment_reference(order_id)
            if order:
                return order

        notes = payment_entity.get("notes")
        if isinstance(notes, dict):
            order_number = str(notes.get("order_number") or "").strip()
            if order_number:
                order = self.orders.get_by_order_number(order_number)
                if order:
                    return order

        receipt = str(order_entity.get("receipt") or "").strip()
        if receipt:
            return self.orders.get_by_order_number(receipt)

        return None

    def _mark_order_paid(
        self,
        order: Order,
        razorpay_order_id: str,
        should_send_confirmation: bool,
    ) -> None:
        if not self._is_final_order_number(order.order_number):
            order.order_number = self._generate_order_number()
        if order.payment_status != "paid":
            self._decrement_inventory_for_order(order)
        order.status = "confirmed"
        order.payment_status = "paid"
        if razorpay_order_id:
            order.payment_reference = razorpay_order_id
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)

        if should_send_confirmation:
            self.email_service.send_order_confirmation(
                buyer_email=order.email,
                subject=f"Order confirmation for {order.order_number}",
                html_body=self._build_email_body(order),
                attachments=[self.build_invoice_attachment(order)],
            )
        self._create_shipment_for_paid_order_best_effort(order)
        GoogleSheetService().sync_successful_orders_snapshot_best_effort()

    def _build_order(
        self,
        payload: OrderCreateRequest,
        order_number: Optional[str] = None,
    ) -> Order:
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
            if int(variant.stock_quantity) <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{self._build_product_display_name(product.name, product.flavour)} ({variant.weight_label}) is out of stock.",
                )
            if item.quantity > int(variant.stock_quantity):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Only {int(variant.stock_quantity)} item(s) left for "
                        f"{self._build_product_display_name(product.name, product.flavour)} ({variant.weight_label})."
                    ),
                )

            line_total = float(variant.selling_price) * item.quantity
            total_amount += line_total
            order_items.append(
                OrderItem(
                    product_slug=product.slug,
                    variant_id=variant.id,
                    product_name=product.name,
                    flavour=product.flavour,
                    variant_label=variant.weight_label,
                    mrp=float(variant.mrp),
                    unit_price=float(variant.selling_price),
                    quantity=item.quantity,
                    line_total=line_total,
                )
            )

        return Order(
            order_number=order_number or self._generate_order_number(),
            total_amount=total_amount,
            customer_name=payload.customer_name,
            email=payload.email,
            phone_number=payload.phone_number,
            alternate_phone_number=payload.alternate_phone_number,
            delivery_address=payload.delivery_address,
            pincode=payload.pincode,
            city=payload.city,
            state=payload.state,
            comments=payload.comments,
            items=order_items,
        )

    def list_customer_orders(self, user: User) -> list[CustomerOrderRead]:
        orders = self.orders.list_orders_by_email(user.email)
        for order in orders:
            self._refresh_tracking_for_order_best_effort(order)
        return [self._build_customer_order_read(order) for order in orders]

    def list_admin_customer_portfolio(self, period: str = "all_time") -> list[AdminCustomerPortfolioRead]:
        portfolio: list[AdminCustomerPortfolioRead] = []
        for order in self.orders.list_orders():
            if not self._is_successful_order(order) or not self._matches_period(order.created_at, period):
                continue
            product_labels = [
                f"{item.product_name} ({item.variant_label}) x {item.quantity}" for item in order.items
            ]
            portfolio.append(
                AdminCustomerPortfolioRead(
                    order_number=order.order_number,
                    created_at=order.created_at,
                    customer_name=order.customer_name,
                    delivery_address=order.delivery_address,
                    pincode=order.pincode,
                    payment_mode="Razorpay",
                    only_success=self._is_successful_order(order),
                    amount_count=float(order.total_amount),
                    products=", ".join(product_labels),
                    product_quantity=sum(item.quantity for item in order.items),
                    product_count=len(order.items),
                    phone_number=order.phone_number,
                    email=order.email,
                    status=order.status,
                    payment_status=order.payment_status,
                )
            )
        return portfolio

    def list_coupon_order_summary(self, period: str = "all_time") -> list[AdminCouponOrderSummaryRead]:
        grouped: dict[str, dict[str, object]] = {}
        for order in self.orders.list_orders():
            if (
                not self._is_successful_order(order)
                or not self._matches_period(order.created_at, period)
                or not order.coupon_code
            ):
                continue

            coupon_code = order.coupon_code.strip().upper()
            bucket = grouped.setdefault(
                coupon_code,
                {
                    "orders_count": 0,
                    "total_revenue": 0.0,
                    "total_products_sold": 0,
                    "order_numbers": [],
                },
            )
            bucket["orders_count"] = int(bucket["orders_count"]) + 1
            bucket["total_revenue"] = float(bucket["total_revenue"]) + float(order.total_amount)
            bucket["total_products_sold"] = int(bucket["total_products_sold"]) + sum(
                item.quantity for item in order.items
            )
            order_numbers = bucket["order_numbers"]
            assert isinstance(order_numbers, list)
            order_numbers.append(order.order_number)

        return sorted(
            [
                AdminCouponOrderSummaryRead(
                    coupon_code=coupon_code,
                    orders_count=int(values["orders_count"]),
                    total_revenue=round(float(values["total_revenue"]), 2),
                    total_products_sold=int(values["total_products_sold"]),
                    order_numbers=", ".join(values["order_numbers"]),
                )
                for coupon_code, values in grouped.items()
            ],
            key=lambda item: (-item.orders_count, -item.total_revenue, item.coupon_code),
        )

    @staticmethod
    def _ensure_order_owner(order: Order, user: User) -> None:
        if order.email.lower() != user.email.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This payment does not belong to the logged-in account.",
            )

    @staticmethod
    def _is_successful_order(order: Order) -> bool:
        return order.payment_status == "paid" and order.status != "cancelled"

    @staticmethod
    def _matches_period(created_at: datetime, period: str) -> bool:
        if period == "all_time":
            return True

        now = datetime.utcnow()
        ranges = {
            "last_7_days": now - timedelta(days=7),
            "last_30_days": now - timedelta(days=30),
            "last_90_days": now - timedelta(days=90),
        }
        threshold = ranges.get(period)
        if threshold is None:
            return True
        return created_at >= threshold

    @staticmethod
    def format_order_number(sequence: int) -> str:
        return f"LN-{sequence:02d}"

    @staticmethod
    def _is_final_order_number(order_number: str) -> bool:
        return order_number.startswith("LN-")

    @staticmethod
    def _generate_pending_order_number() -> str:
        return f"PENDING-{uuid4().hex[:12].upper()}"

    def _generate_order_number(self) -> str:
        sequence = self.orders.get_next_order_sequence(self.settings.order_number_start)
        return self.format_order_number(sequence)

    def _build_customer_order_read(self, order: Order) -> CustomerOrderRead:
        shipment = None
        if order.shipment_provider or order.shipment_status or order.awb_number or order.shipment_error:
            history = [
                ShipmentTrackingEventRead(
                    status=str(item.get("status") or "").strip() or "Update",
                    location=self._string_or_none(item.get("location")),
                    timestamp=self._string_or_none(item.get("timestamp")),
                )
                for item in self._deserialize_tracking_history(order.shipment_tracking_history)
            ]
            shipment = CustomerOrderShipmentRead(
                provider=order.shipment_provider or "GenZLogix",
                order_id=order.shipment_order_id,
                awb_number=order.awb_number,
                status=order.shipment_status,
                courier=order.shipment_courier,
                label_url=order.shipment_label_url,
                estimated_delivery=order.shipment_estimated_delivery.isoformat()
                if order.shipment_estimated_delivery
                else None,
                error=order.shipment_error,
                last_synced_at=order.shipment_last_synced_at.isoformat()
                if order.shipment_last_synced_at
                else None,
                history=history,
            )

        return CustomerOrderRead(
            order_number=order.order_number,
            status=order.status,
            payment_status=order.payment_status,
            total_amount=float(order.total_amount),
            customer_name=order.customer_name,
            email=order.email,
            phone_number=order.phone_number,
            alternate_phone_number=order.alternate_phone_number,
            delivery_address=order.delivery_address,
            pincode=order.pincode,
            city=order.city,
            state=order.state,
            comments=order.comments,
            items=[item for item in order.items],
            shipment=shipment,
        )

    def _ensure_delivery_serviceable(self, delivery_pincode: str) -> dict[str, Any]:
        cleaned_pincode = delivery_pincode.strip()
        if len(cleaned_pincode) != 6 or not cleaned_pincode.isdigit():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Enter a valid 6-digit Indian pincode.",
            )
        if not self.shipping_service.is_configured():
            return {
                "is_serviceable": True,
                "pickup_pincode": self.settings.genzlogix_pickup_pincode,
                "delivery_pincode": cleaned_pincode,
            }

        data = self.shipping_service.check_serviceability(cleaned_pincode)
        if not bool(data.get("is_serviceable")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PINCODE IS NOT YET IN OUR SERVICEBALE LOCATION",
            )
        return data

    def _create_shipment_for_paid_order_best_effort(self, order: Order) -> None:
        if order.payment_status != "paid":
            return
        if order.shipment_order_id:
            return
        if not self.shipping_service.is_configured():
            return

        try:
            shipment_data = self.shipping_service.create_order(self._build_shipping_order_payload(order))
        except HTTPException as error:
            order.shipment_provider = "GenZLogix"
            order.shipment_error = error.detail if isinstance(error.detail, str) else "Shipment creation failed."
            self.db.add(order)
            self.db.commit()
            self.db.refresh(order)
            return

        self._apply_shipment_creation_data(order, shipment_data)

    def _refresh_tracking_for_order_best_effort(self, order: Order) -> None:
        if not order.awb_number or not self.shipping_service.is_configured():
            return

        try:
            tracking_data = self.shipping_service.track_shipment(order.awb_number)
        except HTTPException as error:
            order.shipment_error = error.detail if isinstance(error.detail, str) else "Tracking refresh failed."
            self.db.add(order)
            self.db.commit()
            self.db.refresh(order)
            return

        self._apply_tracking_data(order, tracking_data)

    def _build_shipping_order_payload(self, order: Order) -> dict[str, Any]:
        total_weight = round(sum(self._parse_weight_kg(item.variant_label) * item.quantity for item in order.items), 3)
        return {
            "order_reference": order.order_number,
            "payment_mode": "PREPAID",
            "cod_amount": 0,
            "customer": {
                "name": order.customer_name,
                "email": order.email,
                "phone": order.phone_number,
            },
            "drop_details": {
                "address": order.delivery_address,
                "city": order.city,
                "state": order.state,
                "pincode": order.pincode,
            },
            "package": {
                "weight_kg": total_weight or 0.5,
                "length_cm": self.settings.genzlogix_default_length_cm,
                "breadth_cm": self.settings.genzlogix_default_breadth_cm,
                "height_cm": self.settings.genzlogix_default_height_cm,
            },
            "items": [
                {
                    "name": self._get_item_display_name(item),
                    "sku": item.product_slug or item.product_name[:20].upper().replace(" ", "-"),
                    "qty": item.quantity,
                    "price": float(item.unit_price),
                }
                for item in order.items
            ],
        }

    def _apply_shipment_creation_data(self, order: Order, shipment_data: dict[str, Any]) -> None:
        order.shipment_provider = "GenZLogix"
        order.shipment_order_id = self._string_or_none(shipment_data.get("order_id"))
        order.shipment_status = self._string_or_none(shipment_data.get("status")) or "PENDING"
        order.awb_number = self._string_or_none(shipment_data.get("awb_number"))
        order.shipment_label_url = self._string_or_none(shipment_data.get("label_url"))
        order.shipment_created_at = self._parse_iso_datetime(shipment_data.get("created_at"))
        order.shipment_error = None
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)

        if order.awb_number:
            self._refresh_tracking_for_order_best_effort(order)

    def _apply_tracking_data(self, order: Order, tracking_data: dict[str, Any]) -> None:
        history = tracking_data.get("history")
        order.shipment_provider = "GenZLogix"
        order.awb_number = self._string_or_none(tracking_data.get("awb_number")) or order.awb_number
        order.shipment_status = self._string_or_none(tracking_data.get("current_status")) or order.shipment_status
        order.shipment_courier = self._string_or_none(tracking_data.get("courier"))
        order.shipment_estimated_delivery = self._parse_date_value(tracking_data.get("estimated_delivery"))
        order.shipment_last_synced_at = datetime.utcnow()
        order.shipment_error = None
        if isinstance(history, list):
            normalized_history = [item for item in history if isinstance(item, dict)]
            order.shipment_tracking_history = json.dumps(
                normalized_history,
                separators=(",", ":"),
                ensure_ascii=True,
            )
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)

    @staticmethod
    def _parse_weight_kg(label: str) -> float:
        cleaned = (label or "").strip().lower()
        try:
            if cleaned.endswith("kg"):
                return float(cleaned[:-2].strip() or 0)
            if cleaned.endswith("g"):
                grams = float(cleaned[:-1].strip() or 0)
                return round(grams / 1000, 3)
        except ValueError:
            return 0.5
        return 0.5

    @staticmethod
    def _string_or_none(value: Any) -> Optional[str]:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None

    @staticmethod
    def _int_or_none(value: Any) -> Optional[int]:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _float_or_none(value: Any) -> Optional[float]:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _bool_or_none(value: Any) -> Optional[bool]:
        if value is None:
            return None
        return bool(value)

    @staticmethod
    def _parse_iso_datetime(value: Any) -> Optional[datetime]:
        if not value:
            return None
        try:
            normalized = str(value).replace("Z", "+00:00")
            return datetime.fromisoformat(normalized)
        except ValueError:
            return None

    @staticmethod
    def _parse_date_value(value: Any) -> Optional[date]:
        if not value:
            return None
        try:
            return date.fromisoformat(str(value))
        except ValueError:
            return None

    @staticmethod
    def _deserialize_tracking_history(value: Optional[str]) -> list[dict[str, Any]]:
        if not value:
            return []
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return []
        if not isinstance(decoded, list):
            return []
        return [item for item in decoded if isinstance(item, dict)]

    def _decrement_inventory_for_order(self, order: Order) -> None:
        for item in order.items:
            if not item.product_slug or item.variant_id is None:
                continue
            product = self.products.get_by_slug(item.product_slug)
            if not product:
                continue
            variant = next((candidate for candidate in product.variants if candidate.id == item.variant_id), None)
            if not variant:
                continue
            if int(variant.stock_quantity) < item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Inventory changed before payment confirmation for "
                        f"{self._build_product_display_name(product.name, product.flavour)} ({variant.weight_label})."
                    ),
                )
            variant.stock_quantity = int(variant.stock_quantity) - item.quantity
            self.db.add(variant)

    @staticmethod
    def _build_product_display_name(name: str, flavour: str) -> str:
        name_clean = name.strip()
        flavour_clean = flavour.strip()
        if not flavour_clean:
            return name_clean
        if flavour_clean.lower() in name_clean.lower():
            return name_clean
        return f"{name_clean} - {flavour_clean}"

    @classmethod
    def _get_item_display_name(cls, item: OrderItem) -> str:
        product_name = cls._build_product_display_name(item.product_name, item.flavour)
        variant_label = (item.variant_label or "").strip()
        if not variant_label:
            return product_name
        return f"{product_name} ({variant_label})"

    @classmethod
    def _format_currency(cls, amount: float) -> str:
        return f"Rs. {amount:.2f}"

    @classmethod
    def _calculate_discount_percent(cls, mrp: float, selling_price: float) -> int:
        if mrp <= 0 or selling_price >= mrp:
            return 0
        return int(round(((mrp - selling_price) / mrp) * 100))

    @classmethod
    def _amount_in_words(cls, amount: float) -> str:
        number = int(round(amount))
        if number == 0:
            return "Rupees Zero Only"

        ones = [
            "",
            "One",
            "Two",
            "Three",
            "Four",
            "Five",
            "Six",
            "Seven",
            "Eight",
            "Nine",
            "Ten",
            "Eleven",
            "Twelve",
            "Thirteen",
            "Fourteen",
            "Fifteen",
            "Sixteen",
            "Seventeen",
            "Eighteen",
            "Nineteen",
        ]
        tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

        def below_thousand(value: int) -> str:
            words: list[str] = []
            if value >= 100:
                words.append(f"{ones[value // 100]} Hundred")
                value %= 100
            if value >= 20:
                words.append(tens[value // 10])
                if value % 10:
                    words.append(ones[value % 10])
            elif value > 0:
                words.append(ones[value])
            return " ".join(part for part in words if part)

        parts: list[str] = []
        for divisor, label in ((10000000, "Crore"), (100000, "Lakh"), (1000, "Thousand")):
            chunk = number // divisor
            if chunk:
                parts.append(f"{below_thousand(chunk)} {label}")
                number %= divisor
        if number:
            parts.append(below_thousand(number))
        return f"Rupees {' '.join(parts).strip()} Only"

    @classmethod
    def _wrap_text(cls, value: str, max_chars: int) -> list[str]:
        words = " ".join(value.split()).split(" ")
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = word if not current else f"{current} {word}"
            if len(candidate) <= max_chars:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines or [""]

    @classmethod
    def _build_invoice_rows(cls, order: Order) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for item in order.items:
            mrp = float(item.mrp or item.unit_price)
            unit_price = float(item.unit_price)
            discount_per_unit = max(0.0, mrp - unit_price)
            rows.append(
                {
                    "name_lines": cls._wrap_text(cls._get_item_display_name(item), 34),
                    "hsn": cls.FIXED_HSN_CODE,
                    "qty": item.quantity,
                    "mrp": mrp,
                    "discount": discount_per_unit * item.quantity,
                    "selling_price": float(item.line_total),
                }
            )
        return rows

    @classmethod
    def _build_email_body(cls, order: Order, invoice_number_override: Optional[str] = None) -> str:
        created_date = order.created_at.strftime("%d-%m-%Y") if order.created_at else ""
        subtotal = float(order.total_amount)
        invoice_number = cls._resolve_invoice_number(order, invoice_number_override)
        taxable_value = round(subtotal / (1 + cls.GST_RATE), 2)
        gst_amount = round(subtotal - taxable_value, 2)
        rows = "".join(
            [
                (
                    f"<tr>"
                    f"<td style='padding:11px;border-bottom:1px solid #e6e7ef;'>{cls._get_item_display_name(item)}</td>"
                    f"<td style='padding:11px;border-bottom:1px solid #e6e7ef;'>{cls.FIXED_HSN_CODE}</td>"
                    f"<td style='padding:11px;border-bottom:1px solid #e6e7ef;text-align:center;'>{item.quantity}</td>"
                    f"<td style='padding:11px;border-bottom:1px solid #e6e7ef;text-align:right;'>{cls._format_currency(float(item.mrp or item.unit_price))}</td>"
                    f"<td style='padding:11px;border-bottom:1px solid #e6e7ef;text-align:right;'>{cls._format_currency(max(0.0, float(item.mrp or item.unit_price) - float(item.unit_price)) * item.quantity)}</td>"
                    f"<td style='padding:11px;border-bottom:1px solid #e6e7ef;text-align:right;'>{cls._format_currency(float(item.line_total))}</td>"
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
            f"<p style='margin:0 0 6px;'>GSTIN: 26BKLPL8910L1ZL</p>"
            f"</td>"
            f"<td style='vertical-align:top;text-align:right;'>"
            f"<p style='margin:0 0 6px;'><strong>Invoice No:</strong> {invoice_number}</p>"
            f"<p style='margin:0;'><strong>Invoice Date:</strong> {created_date}</p>"
            f"</td>"
            f"</tr>"
            f"</table>"
            f"<table style='width:100%;border-collapse:collapse;margin-bottom:16px;'>"
            f"<tr>"
            f"<td style='vertical-align:top;padding-right:12px;'>"
            f"<p style='margin:0 0 8px;font-size:20px;font-weight:700;color:#1f1f57;'>Bill To</p>"
            f"<p style='margin:0 0 6px;'><strong>Customer Name:</strong> {order.customer_name}</p>"
            f"<p style='margin:0 0 6px;'><strong>Mobile:</strong> {order.phone_number}</p>"
            f"<p style='margin:0 0 6px;'><strong>Address:</strong> {order.delivery_address}</p>"
            f"<p style='margin:0 0 6px;'><strong>PIN Code:</strong> {order.pincode}</p>"
            f"<p style='margin:0;'><strong>Email:</strong> {order.email}</p>"
            f"</td>"
            f"<td style='vertical-align:top;text-align:right;'>"
            f"<p style='margin:0 0 8px;font-size:20px;font-weight:700;color:#1f1f57;'>Payment Status</p>"
            f"<p style='margin:0 0 6px;'>Paid via Razorpay</p>"
            f"<p style='margin:0;'>Delivery Charges: FREE</p>"
            f"</td>"
            f"</tr>"
            f"</table>"
            f"<table style='width:100%;border-collapse:collapse;border:1px solid #e6e7ef;margin-top:8px;'>"
            f"<thead style='background:#8f87e4;color:#ffffff;'>"
            f"<tr><th style='padding:12px;text-align:left;'>Product</th>"
            f"<th style='padding:12px;text-align:left;'>HSN Code</th>"
            f"<th style='padding:12px;text-align:center;'>Qty</th>"
            f"<th style='padding:12px;text-align:right;'>MRP</th>"
            f"<th style='padding:12px;text-align:right;'>Discount</th>"
            f"<th style='padding:12px;text-align:right;'>Selling Price (Incl. GST)</th></tr></thead>"
            f"<tbody>{rows}</tbody>"
            f"<tfoot>"
            f"<tr><td colspan='2' style='padding:12px;font-weight:700;'>Grand Total</td>"
            f"<td style='padding:12px;text-align:center;font-weight:700;'>{sum(item.quantity for item in order.items)}</td>"
            f"<td colspan='3' style='padding:12px;text-align:right;font-weight:700;'>{cls._format_currency(subtotal)}</td></tr>"
            f"</tfoot></table>"
            f"<table style='width:100%;border-collapse:collapse;margin-top:18px;border:1px solid #e6e7ef;'>"
            f"<tr><td style='padding:10px;font-weight:700;'>Taxable Value</td><td style='padding:10px;text-align:right;'>{cls._format_currency(taxable_value)}</td></tr>"
            f"<tr><td style='padding:10px;font-weight:700;'>GST @ 5%</td><td style='padding:10px;text-align:right;'>{cls._format_currency(gst_amount)}</td></tr>"
            f"<tr style='background:#8f87e4;color:#fff;font-weight:700;'><td style='padding:10px;'>Grand Total</td><td style='padding:10px;text-align:right;'>{cls._format_currency(subtotal)}</td></tr>"
            f"</table>"
            f"<p style='margin:18px 0 0;'><strong>Amount in Words:</strong> {cls._amount_in_words(subtotal)}</p>"
            f"<p style='margin:18px 0 0;font-weight:700;'>Payment Details</p>"
            f"<p style='margin:0 0 6px;'>Payment Mode: Razorpay / UPI / Card</p>"
            f"<p style='margin:0 0 6px;'>Payment Status: Paid</p>"
            f"<p style='margin:0 0 6px;'>Received: {cls._format_currency(subtotal)}</p>"
            f"<p style='margin:0 0 6px;'>Balance: {cls._format_currency(0.0)}</p>"
            f"<p style='margin:18px 0 6px;font-weight:700;'>Declaration</p>"
            f"<p style='margin:0 0 4px;'>Prices are inclusive of GST.</p>"
            f"<p style='margin:0 0 4px;'>Free delivery.</p>"
            f"<p style='margin:0;'>This is a computer-generated invoice and does not require a signature.</p>"
            f"<p style='margin:22px 0 0;color:#4b5563;'>A PDF invoice is attached for your records.</p>"
            f"</div>"
        )

    @classmethod
    def build_invoice_email_body(
        cls,
        order: Order,
        invoice_number_override: Optional[str] = None,
    ) -> str:
        return cls._build_email_body(order, invoice_number_override)

    @classmethod
    def _build_payment_failure_email_body(cls, order: Order, reason: str) -> str:
        checkout_reference = cls._build_checkout_reference(order)
        return (
            f"<div style='font-family:Arial,sans-serif;max-width:720px;margin:0 auto;color:#111827;'>"
            f"<h2 style='margin-bottom:8px;'>Payment could not be completed</h2>"
            f"<p style='margin-top:0;'>Checkout <strong>{checkout_reference}</strong> is marked as payment failed.</p>"
            f"<div style='background:#fef2f2;border:1px solid #fecaca;border-radius:12px;padding:16px;margin:20px 0;'>"
            f"<p style='margin:0 0 8px;'><strong>Reason:</strong> {reason}</p>"
            f"<p style='margin:0 0 8px;'><strong>Customer:</strong> {order.customer_name}</p>"
            f"<p style='margin:0 0 8px;'><strong>Email:</strong> {order.email}</p>"
            f"<p style='margin:0 0 8px;'><strong>Phone:</strong> {order.phone_number}</p>"
            f"<p style='margin:0 0 8px;'><strong>Delivery Address:</strong> {order.delivery_address}</p>"
            f"<p style='margin:0;'><strong>PIN Code:</strong> {order.pincode}</p>"
            f"</div>"
            f"<p>You can retry the payment from the website if needed.</p>"
            f"</div>"
        )

    @classmethod
    def _build_checkout_reference(cls, order: Order) -> str:
        return order.payment_reference or order.order_number

    @classmethod
    def _build_payment_failure_subject(cls, order: Order) -> str:
        return f"Payment failed for checkout {cls._build_checkout_reference(order)}"

    @classmethod
    def _resolve_invoice_number(cls, order: Order, invoice_number_override: Optional[str] = None) -> str:
        return invoice_number_override or order.order_number

    @classmethod
    def build_invoice_attachment(
        cls,
        order: Order,
        invoice_number_override: Optional[str] = None,
    ) -> tuple[str, bytes, str, str]:
        invoice_number = cls._resolve_invoice_number(order, invoice_number_override)
        filename = f"{invoice_number}.pdf"
        return (filename, cls._render_invoice_pdf(order, invoice_number_override), "application", "pdf")

    def list_paid_orders_for_date_range(
        self,
        start_date: date,
        end_date: date,
    ) -> list[Order]:
        if end_date < start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date must be on or after start date.",
            )

        start_at = datetime.combine(start_date, time.min)
        end_before = datetime.combine(end_date + timedelta(days=1), time.min)
        return self.orders.list_paid_orders_in_date_range(start_at, end_before)

    @classmethod
    def build_invoice_statement_attachment(
        cls,
        orders: list[Order],
        start_date: date,
        end_date: date,
    ) -> tuple[str, bytes, str, str]:
        filename = cls.build_invoice_statement_filename(start_date, end_date)
        return (
            filename,
            cls.render_invoice_statement_pdf(orders),
            "application",
            "pdf",
        )

    @staticmethod
    def build_invoice_statement_filename(start_date: date, end_date: date) -> str:
        return f"invoice-statement-{start_date.isoformat()}_to_{end_date.isoformat()}.pdf"

    @classmethod
    def render_invoice_statement_pdf(cls, orders: list[Order]) -> bytes:
        page_contents = [cls._build_invoice_page_content(order) for order in orders]
        return cls._build_pdf_document(page_contents)

    @classmethod
    def _render_invoice_pdf(cls, order: Order, invoice_number_override: Optional[str] = None) -> bytes:
        return cls._build_pdf_document(
            [cls._build_invoice_page_content(order, invoice_number_override)]
        )

    @classmethod
    def _build_invoice_page_content(
        cls,
        order: Order,
        invoice_number_override: Optional[str] = None,
    ) -> bytes:
        total_amount = float(order.total_amount)
        invoice_date = order.created_at.strftime("%d/%m/%Y") if order.created_at else ""
        invoice_number = cls._resolve_invoice_number(order, invoice_number_override)
        taxable_value = round(total_amount / (1 + cls.GST_RATE), 2)
        gst_amount = round(total_amount - taxable_value, 2)
        rows = cls._build_invoice_rows(order)

        def text(x: int, y: int, value: str, size: int = 11, bold: bool = False) -> str:
            font = "F2" if bold else "F1"
            return f"BT 0 0 0 rg /{font} {size} Tf {x} {y} Td ({cls._escape_pdf_text(value)}) Tj ET"

        def rect(x: int, y: int, w: int, h: int, rgb: tuple[float, float, float], fill: bool = True) -> str:
            op = "f" if fill else "S"
            return f"q {rgb[0]} {rgb[1]} {rgb[2]} rg {x} {y} {w} {h} re {op} Q"

        def stroke_rect(x: int, y: int, w: int, h: int, line_width: float = 1.0) -> str:
            return f"q {line_width} w {x} {y} {w} {h} re S Q"

        ops: list[str] = []
        ops.append(rect(18, 20, 559, 802, (1, 1, 1), True))
        ops.append(text(30, 804, "LAGAD'S NUTRITION", 18, True))
        ops.append(text(30, 780, "TAX INVOICE", 16, True))
        ops.append(text(30, 758, "GSTIN: 26BKLPL8910L1ZL", 11, True))
        ops.append(text(380, 758, f"Invoice No.: {invoice_number}", 11, True))
        ops.append(text(380, 740, f"Invoice Date: {invoice_date}", 11, True))

        ops.append(text(30, 714, "Bill To", 13, True))
        bill_to_lines = [
            f"Customer Name: {order.customer_name}",
            f"Mobile: {order.phone_number}",
            f"Address: {order.delivery_address}",
            f"PIN Code: {order.pincode}",
            f"Email: {order.email}",
        ]
        bill_y = 694
        for line_value in bill_to_lines:
            for wrapped_line in cls._wrap_text(line_value, 68):
                ops.append(text(30, bill_y, wrapped_line, 10))
                bill_y -= 16

        table_top = bill_y - 8
        column_x = {"product": 32, "hsn": 280, "qty": 360, "mrp": 400, "discount": 462, "selling": 528}
        row_right = 565
        header_height = 28
        ops.append(rect(30, table_top - header_height, 535, header_height, (0.92, 0.92, 0.92), True))
        ops.append(stroke_rect(30, table_top - header_height, 535, header_height))
        ops.append(text(column_x["product"], table_top - 18, "Product", 10, True))
        ops.append(text(column_x["hsn"], table_top - 18, "HSN Code", 10, True))
        ops.append(text(column_x["qty"], table_top - 18, "Qty", 10, True))
        ops.append(text(column_x["mrp"], table_top - 18, "MRP", 10, True))
        ops.append(text(column_x["discount"], table_top - 18, "Discount", 10, True))
        ops.append(text(column_x["selling"], table_top - 18, "Selling", 10, True))

        current_top = table_top - header_height
        for row in rows[:8]:
            name_lines = row["name_lines"]
            assert isinstance(name_lines, list)
            row_height = max(26, 14 + (len(name_lines) * 14))
            current_bottom = current_top - row_height
            ops.append(stroke_rect(30, current_bottom, 535, row_height, 0.8))
            text_y = current_top - 16
            for name_line in name_lines:
                ops.append(text(column_x["product"], text_y, str(name_line), 9, True))
                text_y -= 12
            ops.append(text(column_x["hsn"], current_top - 16, str(row["hsn"]), 9))
            ops.append(text(column_x["qty"], current_top - 16, str(row["qty"]), 9))
            ops.append(text(column_x["mrp"], current_top - 16, cls._format_currency(float(row["mrp"])), 9))
            ops.append(text(column_x["discount"], current_top - 16, cls._format_currency(float(row["discount"])), 9))
            ops.append(text(column_x["selling"], current_top - 16, cls._format_currency(float(row["selling_price"])), 9))
            current_top = current_bottom

        gst_top = current_top - 26
        ops.append(text(30, gst_top, "GST Calculation", 12, True))
        gst_box_top = gst_top - 14
        ops.append(stroke_rect(30, gst_box_top - 84, 250, 84))
        ops.append(text(38, gst_box_top - 18, "Taxable Value", 10, True))
        ops.append(text(180, gst_box_top - 18, cls._format_currency(taxable_value), 10))
        ops.append(text(38, gst_box_top - 42, "GST @ 5%", 10, True))
        ops.append(text(180, gst_box_top - 42, cls._format_currency(gst_amount), 10))
        ops.append(text(38, gst_box_top - 66, "Total (Inclusive of GST)", 10, True))
        ops.append(text(180, gst_box_top - 66, cls._format_currency(total_amount), 10))

        summary_top = gst_top
        ops.append(text(320, summary_top, "Delivery Charges: FREE", 11, True))
        ops.append(text(320, summary_top - 24, f"Grand Total: {cls._format_currency(total_amount)}", 12, True))
        amount_lines = cls._wrap_text(f"Amount in Words: {cls._amount_in_words(total_amount)}", 42)
        amount_y = summary_top - 48
        for amount_line in amount_lines:
            ops.append(text(320, amount_y, amount_line, 10))
            amount_y -= 14

        payment_top = min(gst_box_top - 108, amount_y - 10)
        ops.append(text(30, payment_top, "Payment Details", 12, True))
        payment_lines = [
            "Payment Mode: Razorpay / UPI / Card / Cash",
            "Payment Status: Paid",
            f"Received: {cls._format_currency(total_amount)}",
            f"Balance: {cls._format_currency(0.0)}",
        ]
        y = payment_top - 20
        for payment_line in payment_lines:
            ops.append(text(30, y, payment_line, 10))
            y -= 16

        declaration_top = y - 8
        ops.append(text(30, declaration_top, "Declaration", 12, True))
        declaration_lines = [
            "Prices are inclusive of GST.",
            "Free delivery.",
            "This is a computer-generated invoice and does not require a signature.",
        ]
        y = declaration_top - 20
        for declaration_line in declaration_lines:
            for wrapped_line in cls._wrap_text(declaration_line, 78):
                ops.append(text(30, y, wrapped_line, 10))
                y -= 14

        ops.append(text(390, y - 8, "For Lagad's Nutrition", 11, True))
        ops.append(text(390, 72, "Authorized Signatory", 11, True))

        return "\n".join(ops).encode("latin-1", "replace")

    @classmethod
    def _build_pdf_document(cls, page_contents: list[bytes]) -> bytes:
        if not page_contents:
            raise ValueError("At least one invoice is required to build a PDF document.")

        objects: list[bytes] = [
            b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
            b"2 0 obj\n<< /Type /Pages /Kids [",
        ]
        page_object_ids: list[int] = []
        dynamic_objects: list[bytes] = [
            b"3 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
            b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>\nendobj\n",
        ]

        next_object_id = 5
        for content in page_contents:
            page_object_id = next_object_id
            content_object_id = next_object_id + 1
            page_object_ids.append(page_object_id)

            dynamic_objects.append(
                (
                    f"{page_object_id} 0 obj\n"
                    "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                    "/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> "
                    f"/Contents {content_object_id} 0 R >>\nendobj\n"
                ).encode("ascii")
            )
            dynamic_objects.append(
                (
                    f"{content_object_id} 0 obj\n<< /Length {len(content)} >>\nstream\n".encode("ascii")
                    + content
                    + b"\nendstream\nendobj\n"
                )
            )
            next_object_id += 2

        kids = " ".join(f"{page_object_id} 0 R" for page_object_id in page_object_ids)
        objects[1] = (
            f"2 0 obj\n<< /Type /Pages /Kids [{kids}] /Count {len(page_object_ids)} >>\nendobj\n"
        ).encode("ascii")
        objects.extend(dynamic_objects)

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
