from typing import Optional

from pydantic import BaseModel, EmailStr


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
