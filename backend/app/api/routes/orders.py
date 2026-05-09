from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.order import OrderCreateRequest
from app.services.order_service import OrderService

router = APIRouter()


@router.post("")
def create_order(payload: OrderCreateRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    return OrderService(db).create_order(payload)

