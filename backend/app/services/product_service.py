from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.product import Product, ProductVariant
from app.repositories.product import ProductRepository
from app.schemas.product import ProductCreate


class ProductService:
    def __init__(self, db: Session):
        self.repository = ProductRepository(db)

    def list_products(self) -> list[Product]:
        return self.repository.list_products()

    def create_product(self, payload: ProductCreate) -> Product:
        product = Product(
            slug=payload.slug,
            name=payload.name,
            flavour=payload.flavour,
            description=payload.description,
            image_url=payload.image_url,
            category=payload.category,
            variants=[
                ProductVariant(
                    weight_label=variant.weight_label,
                    mrp=variant.mrp,
                    selling_price=variant.selling_price,
                    stock_quantity=variant.stock_quantity,
                )
                for variant in payload.variants
            ],
        )
        return self.repository.create(product)

    def update_product(self, product_id: int, payload: ProductCreate) -> Product:
        product = self.repository.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        return self.repository.update(product, payload.model_dump())

    def delete_product(self, product_id: int) -> None:
        product = self.repository.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        self.repository.delete(product)
