from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_admin
from app.db.session import get_db
from app.schemas.product import ProductCreate, ProductRead
from app.services.product_service import ProductService

router = APIRouter()
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/products", response_model=list[ProductRead])
def list_admin_products(
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
) -> list[ProductRead]:
    return ProductService(db).list_products()


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


@router.post("/upload-image")
async def upload_product_image(
    file: UploadFile = File(...),
    _admin=Depends(get_current_admin),
) -> dict[str, str]:
    extension = Path(file.filename or "upload.png").suffix or ".png"
    filename = f"{uuid4().hex}{extension}"
    file_path = UPLOAD_DIR / filename
    content = await file.read()
    file_path.write_bytes(content)
    return {"image_url": f"/uploads/{filename}"}
