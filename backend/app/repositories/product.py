from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.product import Product, ProductVariant


class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_products(self) -> list[Product]:
        result = self.db.execute(select(Product).options(selectinload(Product.variants)))
        return list(result.scalars().all())

    def get_by_slug(self, slug: str) -> Optional[Product]:
        result = self.db.execute(
            select(Product).where(Product.slug == slug).options(selectinload(Product.variants))
        )
        return result.scalar_one_or_none()

    def create(self, product: Product) -> Product:
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def get_by_id(self, product_id: int) -> Optional[Product]:
        result = self.db.execute(
            select(Product).where(Product.id == product_id).options(selectinload(Product.variants))
        )
        return result.scalar_one_or_none()

    def update(self, product: Product, payload: dict) -> Product:
        variants = payload.pop("variants", None)
        for key, value in payload.items():
            setattr(product, key, value)

        if variants is not None:
            product.variants.clear()
            product.variants.extend(
                [
                    ProductVariant(
                        weight_label=variant["weight_label"],
                        mrp=variant["mrp"],
                        selling_price=variant["selling_price"],
                        stock_quantity=variant["stock_quantity"],
                    )
                    for variant in variants
                ]
            )

        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def delete(self, product: Product) -> None:
        self.db.delete(product)
        self.db.commit()
