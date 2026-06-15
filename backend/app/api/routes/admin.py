from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_admin
from app.db.session import get_db
from app.schemas.coupon import CouponCreateRequest, CouponRead
from app.schemas.hero import HeroSettingsRead, HeroSettingsUpdate
from app.schemas.order import AdminCouponOrderSummaryRead, AdminCustomerPortfolioRead
from app.schemas.product import ProductCreate, ProductRead
from app.services.coupon_service import CouponService
from app.services.hero_service import HeroService
from app.services.order_service import OrderService
from app.services.product_service import ProductService

router = APIRouter()
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024


@router.get("/products", response_model=list[ProductRead])
def list_admin_products(
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
) -> list[ProductRead]:
    return ProductService(db).list_products()


@router.get("/hero", response_model=HeroSettingsRead)
def get_admin_hero(
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
) -> HeroSettingsRead:
    return HeroService(db).get_settings()


@router.get("/customer-portfolio", response_model=list[AdminCustomerPortfolioRead])
def get_customer_portfolio(
    period: str = "all_time",
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
) -> list[AdminCustomerPortfolioRead]:
    return OrderService(db).list_admin_customer_portfolio(period)


@router.get("/coupon-orders", response_model=list[AdminCouponOrderSummaryRead])
def get_coupon_orders(
    period: str = "all_time",
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
) -> list[AdminCouponOrderSummaryRead]:
    return OrderService(db).list_coupon_order_summary(period)


@router.put("/hero", response_model=HeroSettingsRead)
def update_admin_hero(
    payload: HeroSettingsUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
) -> HeroSettingsRead:
    return HeroService(db).update_settings(payload)


@router.post("/products", response_model=ProductRead)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
) -> ProductRead:
    return ProductService(db).create_product(payload)


@router.get("/coupons", response_model=list[CouponRead])
def list_coupon_codes(
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
) -> list[CouponRead]:
    return CouponService(db).list_codes()


@router.post("/coupons", response_model=CouponRead)
def create_coupon_code(
    payload: CouponCreateRequest,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
) -> CouponRead:
    return CouponService(db).create_code(payload)


@router.delete("/coupons/{code}")
def delete_coupon_code(
    code: str,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
) -> dict[str, str]:
    CouponService(db).delete_code(code)
    return {"message": "Coupon deleted successfully."}


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
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported image type. Please upload JPG, PNG, WEBP, or GIF files.",
        )

    extension = Path(file.filename or "upload.png").suffix or ".png"
    filename = f"{uuid4().hex}{extension}"
    file_path = UPLOAD_DIR / filename
    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded image is empty.",
        )
    if len(content) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image is too large. Please upload a file under 10 MB.",
        )

    file_path.write_bytes(content)
    return {"image_url": f"/uploads/{filename}"}
