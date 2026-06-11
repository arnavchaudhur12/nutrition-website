from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.visitor_service import VisitorService

router = APIRouter()

@router.get("")
def get_total_visitors(db: Session = Depends(get_db)) -> dict[str, int]:
    return VisitorService(db).get_total_visitors()


@router.post("/track")
def track_total_visitors(db: Session = Depends(get_db)) -> dict[str, int]:
    return VisitorService(db).track_visit()
