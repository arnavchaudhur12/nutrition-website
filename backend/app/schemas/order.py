from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, model_validator


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
    comments: Optional[str] = None
    items: list[OrderItemRequest]


class RazorpayOrderCreateRequest(BaseModel):
    amount: Optional[int] = Field(default=None, ge=100)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    receipt: Optional[str] = Field(default=None, max_length=40)
    customer_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    alternate_phone_number: Optional[str] = None
    delivery_address: Optional[str] = None
    comments: Optional[str] = None
    coupon_code: Optional[str] = None
    items: list[OrderItemRequest] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_payment_source(self) -> "RazorpayOrderCreateRequest":
        if self.items:
            required_fields = {
                "customer_name": self.customer_name,
                "email": self.email,
                "phone_number": self.phone_number,
                "delivery_address": self.delivery_address,
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
    delivery_address: str
    comments: Optional[str] = None
    items: list[OrderItemRead]

    model_config = {"from_attributes": True}


class AdminCustomerPortfolioRead(BaseModel):
    order_number: str
    created_at: datetime
    customer_name: str
    delivery_address: str
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
