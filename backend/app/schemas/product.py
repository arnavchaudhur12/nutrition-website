from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ProductVariantBase(BaseModel):
    weight_label: str = Field(min_length=1, max_length=32)
    mrp: float = Field(gt=0)
    selling_price: float = Field(gt=0)
    stock_quantity: int = Field(default=100, ge=0)

    @field_validator("weight_label")
    @classmethod
    def strip_weight_label(cls, value: str) -> str:
        return value.strip()


class ProductVariantRead(ProductVariantBase):
    id: int

    model_config = {"from_attributes": True}


class ProductImageRead(BaseModel):
    id: int
    image_url: str
    sort_order: int

    model_config = {"from_attributes": True}


class ProductRead(BaseModel):
    id: int
    slug: str
    name: str
    flavour: str
    description: str
    image_url: Optional[str]
    category: str
    images: list[ProductImageRead]
    variants: list[ProductVariantRead]

    model_config = {"from_attributes": True}


class ProductCreate(BaseModel):
    slug: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=120)
    flavour: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1)
    image_url: Optional[str] = None
    image_urls: list[str] = Field(default_factory=list, max_length=5)
    category: str = Field(default="Peanut Butter", min_length=1, max_length=80)
    variants: list[ProductVariantBase] = Field(min_length=1)

    @field_validator("slug", "name", "flavour", "description", "category")
    @classmethod
    def strip_text_fields(cls, value: str) -> str:
        return value.strip()

    @field_validator("image_urls")
    @classmethod
    def validate_image_urls(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]
