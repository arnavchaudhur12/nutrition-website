from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.hero import HeroImage, HeroSettings
from app.schemas.hero import HeroSettingsUpdate


DEFAULT_HERO_IMAGE = "/hero-quote-background.jpeg"


class HeroService:
    def __init__(self, db: Session):
        self.db = db

    def get_settings(self) -> HeroSettings:
        settings = self.db.execute(
            select(HeroSettings).options(selectinload(HeroSettings.images)).limit(1)
        ).scalar_one_or_none()
        if settings:
            if self._strip_legacy_default_image(settings):
                self.db.add(settings)
                self.db.commit()
                self.db.refresh(settings)
            return settings
        return self._create_default_settings()

    def update_settings(self, payload: HeroSettingsUpdate) -> HeroSettings:
        settings = self.get_settings()
        settings.eyebrow_text = payload.eyebrow_text
        settings.headline = payload.headline
        settings.body_text = payload.body_text
        settings.cta_label = payload.cta_label
        settings.cta_link = payload.cta_link
        settings.offer_text = payload.offer_text
        settings.badge_title = payload.badge_title
        settings.badge_subtitle = payload.badge_subtitle
        settings.images.clear()
        settings.images.extend(
            [
                HeroImage(image_url=image_url, sort_order=index)
                for index, image_url in enumerate(payload.image_urls)
                if image_url
            ]
        )
        self.db.add(settings)
        self.db.commit()
        self.db.refresh(settings)
        return self.get_settings()

    def _create_default_settings(self) -> HeroSettings:
        settings = HeroSettings(
            eyebrow_text="Small-batch flavour. Big shelf presence.",
            headline="Healthy Taste For Everyday Lifestyle",
            body_text=(
                "Lagads Nutrition hero copy is now manageable from the admin dashboard so"
                " you can update launches, messages, and campaign visuals without code changes."
            ),
            cta_label="Shop Now",
            cta_link="#products",
            offer_text="Fresh jars. Strong value. Smooth checkout.",
            badge_title="Lagads Nutrition",
            badge_subtitle="Built for everyday lifestyle",
            images=[],
        )
        self.db.add(settings)
        self.db.commit()
        self.db.refresh(settings)
        return settings

    @staticmethod
    def _strip_legacy_default_image(settings: HeroSettings) -> bool:
        legacy_images = [image for image in settings.images if image.image_url == DEFAULT_HERO_IMAGE]
        if not legacy_images:
            return False

        non_legacy_images = [image for image in settings.images if image.image_url != DEFAULT_HERO_IMAGE]
        if non_legacy_images:
            for legacy_image in legacy_images:
                settings.images.remove(legacy_image)
            return True

        settings.images.clear()
        return True
