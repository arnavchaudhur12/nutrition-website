from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.product import Product, ProductImage, ProductVariant
from app.repositories.product import ProductRepository
from app.schemas.product import ProductCreate


class ProductService:
    def __init__(self, db: Session):
        self.repository = ProductRepository(db)

    def list_products(self) -> list[Product]:
        return self.repository.list_products()

    def create_product(self, payload: ProductCreate) -> Product:
        existing = self.repository.get_by_slug(payload.slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A product with this slug already exists.",
            )
        primary_image_url = payload.image_urls[0] if payload.image_urls else payload.image_url
        product = Product(
            slug=payload.slug,
            name=payload.name,
            flavour=payload.flavour,
            description=payload.description,
            image_url=primary_image_url,
            category=payload.category,
            images=[
                ProductImage(image_url=image_url, sort_order=index)
                for index, image_url in enumerate(payload.image_urls)
            ],
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
        existing = self.repository.get_by_slug(payload.slug)
        if existing and existing.id != product_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A product with this slug already exists.",
            )
        if payload.image_urls and payload.image_url != payload.image_urls[0]:
            payload = payload.model_copy(update={"image_url": payload.image_urls[0]})
        return self.repository.update(product, payload.model_dump())

    def delete_product(self, product_id: int) -> None:
        product = self.repository.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        self.repository.delete(product)
