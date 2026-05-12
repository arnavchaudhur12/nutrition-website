from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.hero import HeroImage, HeroSettings
from app.core.config import get_settings
from app.core.security import get_password_hash
from app.models.product import Product, ProductImage, ProductVariant
from app.models.user import User


def seed_defaults(db: Session) -> None:
    settings = get_settings()

    admin = db.execute(select(User).where(User.email == settings.admin_email)).scalar_one_or_none()
    if not admin:
        db.add(
            User(
                email=settings.admin_email,
                full_name="Lagads Nutrition Admin",
                hashed_password=get_password_hash(settings.admin_password),
                is_admin=True,
            )
        )

    has_products = db.execute(select(Product.id)).first()
    if not has_products:
        db.add_all(
            [
                Product(
                    slug="dark-chocolate-crispy",
                    name="Peanut Butter",
                    flavour="Dark Chocolate Crispy",
                    description=(
                        "Lagads Nutrition Dark Chocolate Crispy is built for customers who want an indulgent"
                        " peanut butter experience with a stronger snack personality. The profile combines a"
                        " rich chocolate note, roasted peanut depth, and a crisp bite that makes each spoonful"
                        " feel more layered and satisfying. It works especially well for breakfast bowls, toast,"
                        " smoothies, waffles, and quick evening cravings where texture matters as much as taste."
                        " The 1kg jar is ideal for households and repeat buyers, while the 500g pack is perfect"
                        " for discovery and routine weekday use."
                    ),
                    category="Peanut Butter",
                    variants=[
                        ProductVariant(weight_label="1kg", mrp=699, selling_price=500, stock_quantity=100),
                        ProductVariant(weight_label="500g", mrp=375, selling_price=350, stock_quantity=100),
                    ],
                ),
                Product(
                    slug="mawa-malai-creamy",
                    name="Peanut Butter",
                    flavour="Mawa Malai Creamy",
                    description=(
                        "Lagads Nutrition Mawa Malai Creamy is designed for a softer, richer, more dessert-led"
                        " experience with a smooth finish that spreads beautifully and blends easily into shakes,"
                        " fruit bowls, and toast. It has a mellow profile that feels comforting and premium,"
                        " making it a strong everyday product for customers who prefer creamy textures over"
                        " crunch. The 1kg option delivers stronger value for heavy users and families, while the"
                        " 500g jar gives first-time buyers an approachable entry point into the range."
                    ),
                    category="Peanut Butter",
                    variants=[
                        ProductVariant(weight_label="1kg", mrp=719, selling_price=530, stock_quantity=100),
                        ProductVariant(weight_label="500g", mrp=389, selling_price=370, stock_quantity=100),
                    ],
                ),
            ]
        )

    products = db.execute(select(Product)).scalars().all()
    for product in products:
        if product.image_url and not product.images:
            product.images.append(ProductImage(image_url=product.image_url, sort_order=0))

    hero_settings = db.execute(select(HeroSettings)).scalar_one_or_none()
    if not hero_settings:
        db.add(
            HeroSettings(
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
                images=[HeroImage(image_url="/hero-quote-background.jpeg", sort_order=0)],
            )
        )

    db.commit()
