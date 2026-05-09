from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.models.product import Product, ProductVariant
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

    db.commit()

