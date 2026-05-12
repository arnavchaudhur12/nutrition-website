from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class HeroSettings(Base):
    __tablename__ = "hero_settings"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    eyebrow_text: Mapped[str] = mapped_column(String(160))
    headline: Mapped[str] = mapped_column(String(240))
    body_text: Mapped[str] = mapped_column(Text)
    cta_label: Mapped[str] = mapped_column(String(80), default="Shop Now")
    cta_link: Mapped[str] = mapped_column(String(240), default="#products")
    offer_text: Mapped[str] = mapped_column(String(240), default="Fresh jars. Strong value. Smooth checkout.")
    badge_title: Mapped[str] = mapped_column(String(160))
    badge_subtitle: Mapped[str] = mapped_column(String(160))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    images: Mapped[list["HeroImage"]] = relationship(
        back_populates="hero_settings",
        cascade="all, delete-orphan",
        order_by="HeroImage.sort_order",
    )


class HeroImage(Base):
    __tablename__ = "hero_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    hero_settings_id: Mapped[int] = mapped_column(ForeignKey("hero_settings.id"))
    image_url: Mapped[str] = mapped_column(String(500))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    hero_settings: Mapped["HeroSettings"] = relationship(back_populates="images")
