from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_admin
from app.db.session import get_db
from app.schemas.product import ProductCreate, ProductRead
from app.services.product_service import ProductService

router = APIRouter()


@router.post("/products", response_model=ProductRead)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
) -> ProductRead:
    return ProductService(db).create_product(payload)


@router.put("/products/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int,
    payload: ProductCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
) -> ProductRead:
    return ProductService(db).update_product(product_id, payload)


@router.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
) -> dict[str, str]:
    ProductService(db).delete_product(product_id)
    return {"message": "Product deleted successfully."}
