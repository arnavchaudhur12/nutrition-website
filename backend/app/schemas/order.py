from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

INDIAN_PHONE_REGEX = r"^[6-9]\d{9}$"
INDIAN_PINCODE_REGEX = r"^[1-9]\d{5}$"


class OrderItemRequest(BaseModel):
    product_slug: str
    variant_id: int
    quantity: int


class OrderCreateRequest(BaseModel):
    customer_name: str
    email: EmailStr
    phone_number: str
    alternate_phone_number: Optional[str] = None
    delivery_address: str
    pincode: str
    city: str
    state: str
    comments: Optional[str] = None
    items: list[OrderItemRequest]

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) != 10 or not cleaned.isdigit() or cleaned[0] not in "6789":
            raise ValueError("Phone number must be a valid 10-digit Indian mobile number.")
        return cleaned

    @field_validator("alternate_phone_number")
    @classmethod
    def validate_alternate_phone_number(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        cleaned = value.strip()
        if not cleaned:
            return None
        if len(cleaned) != 10 or not cleaned.isdigit() or cleaned[0] not in "6789":
            raise ValueError("Alternative phone number must be a valid 10-digit Indian mobile number.")
        return cleaned

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) != 6 or not cleaned.isdigit() or cleaned[0] == "0":
            raise ValueError("Pincode must be a valid 6-digit Indian pincode.")
        return cleaned

    @field_validator("city", "state")
    @classmethod
    def validate_location_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("City and state are required.")
        return cleaned


class RazorpayOrderCreateRequest(BaseModel):
    amount: Optional[int] = Field(default=None, ge=100)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    receipt: Optional[str] = Field(default=None, max_length=40)
    customer_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    alternate_phone_number: Optional[str] = None
    delivery_address: Optional[str] = None
    pincode: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    comments: Optional[str] = None
    coupon_code: Optional[str] = None
    items: list[OrderItemRequest] = Field(default_factory=list)

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        cleaned = value.strip()
        if len(cleaned) != 10 or not cleaned.isdigit() or cleaned[0] not in "6789":
            raise ValueError("Phone number must be a valid 10-digit Indian mobile number.")
        return cleaned

    @field_validator("alternate_phone_number")
    @classmethod
    def validate_alternate_phone_number(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        cleaned = value.strip()
        if not cleaned:
            return None
        if len(cleaned) != 10 or not cleaned.isdigit() or cleaned[0] not in "6789":
            raise ValueError("Alternative phone number must be a valid 10-digit Indian mobile number.")
        return cleaned

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        cleaned = value.strip()
        if len(cleaned) != 6 or not cleaned.isdigit() or cleaned[0] == "0":
            raise ValueError("Pincode must be a valid 6-digit Indian pincode.")
        return cleaned

    @field_validator("city", "state")
    @classmethod
    def validate_optional_location_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        cleaned = value.strip()
        if not cleaned:
            return None
        return cleaned

    @model_validator(mode="after")
    def validate_payment_source(self) -> "RazorpayOrderCreateRequest":
        if self.items:
            required_fields = {
                "customer_name": self.customer_name,
                "email": self.email,
                "phone_number": self.phone_number,
                "delivery_address": self.delivery_address,
                "pincode": self.pincode,
                "city": self.city,
                "state": self.state,
            }
            missing_fields = [field for field, value in required_fields.items() if not value]
            if missing_fields:
                raise ValueError(f"Missing checkout fields: {', '.join(missing_fields)}")
            return self

        if self.amount is None:
            raise ValueError("Amount is required when checkout items are not provided.")
        return self


class RazorpayOrderRead(BaseModel):
    order_id: str
    amount: int
    currency: str
    receipt: Optional[str] = None
    app_order_number: Optional[str] = None


class RazorpayVerifyRequest(BaseModel):
    razorpay_payment_id: Optional[str] = None
    razorpay_order_id: Optional[str] = None
    razorpay_signature: Optional[str] = None


class RazorpayVerifyRead(BaseModel):
    success: bool
    order_number: Optional[str] = None


class RazorpayFailureRequest(BaseModel):
    razorpay_order_id: str = Field(min_length=1)
    razorpay_payment_id: Optional[str] = None
    reason: Optional[str] = None
    description: Optional[str] = None


class ServiceabilityRead(BaseModel):
    is_serviceable: bool
    pickup_pincode: str
    delivery_pincode: str
    estimated_delivery_days: Optional[int] = None
    cod_available: Optional[bool] = None
    available_couriers: list[str] = Field(default_factory=list)
    min_rate: Optional[float] = None


class OrderRead(BaseModel):
    order_number: str
    status: str
    payment_status: str
    total_amount: float


class OrderItemRead(BaseModel):
    product_name: str
    flavour: str
    variant_label: str
    unit_price: float
    quantity: int
    line_total: float

    model_config = {"from_attributes": True}


class CustomerOrderRead(BaseModel):
    order_number: str
    status: str
    payment_status: str
    total_amount: float
    customer_name: str
    email: EmailStr
    phone_number: str
    alternate_phone_number: Optional[str] = None
    delivery_address: str
    pincode: str
    city: str
    state: str
    comments: Optional[str] = None
    items: list[OrderItemRead]
    shipment: Optional["CustomerOrderShipmentRead"] = None

    model_config = {"from_attributes": True}


class ShipmentTrackingEventRead(BaseModel):
    status: str
    location: Optional[str] = None
    timestamp: Optional[str] = None


class CustomerOrderShipmentRead(BaseModel):
    provider: str
    order_id: Optional[str] = None
    awb_number: Optional[str] = None
    status: Optional[str] = None
    courier: Optional[str] = None
    label_url: Optional[str] = None
    estimated_delivery: Optional[str] = None
    error: Optional[str] = None
    last_synced_at: Optional[str] = None
    history: list[ShipmentTrackingEventRead] = Field(default_factory=list)


CustomerOrderRead.model_rebuild()


class AdminCustomerPortfolioRead(BaseModel):
    order_number: str
    created_at: datetime
    customer_name: str
    delivery_address: str
    pincode: str
    payment_mode: str
    only_success: bool
    amount_count: float
    products: str
    product_quantity: int
    product_count: int
    phone_number: str
    email: EmailStr
    status: str
    payment_status: str


class AdminCouponOrderSummaryRead(BaseModel):
    coupon_code: str
    orders_count: int
    total_revenue: float
    total_products_sold: int
    order_numbers: str
