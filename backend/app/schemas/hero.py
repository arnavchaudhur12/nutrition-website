from pydantic import BaseModel, Field, field_validator


class HeroImageRead(BaseModel):
    id: int
    image_url: str
    sort_order: int

    model_config = {"from_attributes": True}


class HeroSettingsRead(BaseModel):
    eyebrow_text: str
    headline: str
    body_text: str
    cta_label: str
    cta_link: str
    offer_text: str
    badge_title: str
    badge_subtitle: str
    images: list[HeroImageRead]

    model_config = {"from_attributes": True}


class HeroSettingsUpdate(BaseModel):
    eyebrow_text: str = Field(min_length=1, max_length=160)
    headline: str = Field(min_length=1, max_length=240)
    body_text: str = Field(min_length=1)
    cta_label: str = Field(min_length=1, max_length=80)
    cta_link: str = Field(min_length=1, max_length=240)
    offer_text: str = Field(min_length=1, max_length=240)
    badge_title: str = Field(min_length=1, max_length=160)
    badge_subtitle: str = Field(min_length=1, max_length=160)
    image_urls: list[str] = Field(min_length=1, max_length=5)

    @field_validator(
        "eyebrow_text",
        "headline",
        "body_text",
        "cta_label",
        "cta_link",
        "offer_text",
        "badge_title",
        "badge_subtitle",
    )
    @classmethod
    def strip_text_fields(cls, value: str) -> str:
        return value.strip()

    @field_validator("image_urls")
    @classmethod
    def clean_image_urls(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("At least one hero image is required.")
        return cleaned[:5]
