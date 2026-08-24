import re
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


def slugify_product_name(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    return slug.strip("-")


def number_or_none(value: Any) -> Optional[float]:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return None


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

    @model_validator(mode="before")
    @classmethod
    def normalize_admin_payload(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        normalized = dict(data)
        name = str(normalized.get("name") or "").strip()
        flavour = str(normalized.get("flavour") or "").strip()
        slug = str(normalized.get("slug") or "").strip()
        description = str(normalized.get("description") or "").strip()

        if not slug and name:
            normalized["slug"] = slugify_product_name(name)
        if not description:
            normalized["description"] = " - ".join(part for part in (name, flavour) if part)

        variants = normalized.get("variants")
        if isinstance(variants, list):
            normalized["variants"] = [
                variant
                for variant in variants
                if not (
                    isinstance(variant, dict)
                    and (mrp := number_or_none(variant.get("mrp"))) is not None
                    and (selling_price := number_or_none(variant.get("selling_price"))) is not None
                    and mrp <= 0
                    and selling_price <= 0
                )
            ]

        return normalized

    @field_validator("image_urls")
    @classmethod
    def validate_image_urls(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]
