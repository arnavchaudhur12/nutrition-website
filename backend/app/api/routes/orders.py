from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.order import CustomerOrderRead, OrderCreateRequest
from app.services.order_service import OrderService

router = APIRouter()


@router.post("")
def create_order(payload: OrderCreateRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    return OrderService(db).create_order(payload)


@router.get("/my", response_model=list[CustomerOrderRead])
def list_my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CustomerOrderRead]:
    return OrderService(db).list_customer_orders(current_user)
