from typing import Optional

from pydantic import BaseModel


class ProductVariantBase(BaseModel):
    weight_label: str
    mrp: float
    selling_price: float
    stock_quantity: int = 100


class ProductVariantRead(ProductVariantBase):
    id: int

    model_config = {"from_attributes": True}


class ProductRead(BaseModel):
    id: int
    slug: str
    name: str
    flavour: str
    description: str
    image_url: Optional[str]
    category: str
    variants: list[ProductVariantRead]

    model_config = {"from_attributes": True}


class ProductCreate(BaseModel):
    slug: str
    name: str
    flavour: str
    description: str
    image_url: Optional[str] = None
    category: str = "Peanut Butter"
    variants: list[ProductVariantBase]
