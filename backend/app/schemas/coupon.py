from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class CouponCreateRequest(BaseModel):
    code: str = Field(min_length=6, max_length=6)
    discount_percent: int = Field(ge=1, le=90)

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        normalized = value.strip().upper()
        if len(normalized) != 6 or not normalized.isalnum():
            raise ValueError("Coupon code must be exactly 6 alphanumeric characters.")
        return normalized


class CouponRead(BaseModel):
    id: int
    code: str
    discount_percent: int
    created_at: datetime

    model_config = {"from_attributes": True}

