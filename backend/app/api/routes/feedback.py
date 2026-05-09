from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.feedback import Feedback
from app.schemas.feedback import FeedbackCreate

router = APIRouter()


@router.post("")
def create_feedback(payload: FeedbackCreate, db: Session = Depends(get_db)) -> dict[str, str]:
    feedback = Feedback(**payload.model_dump())
    db.add(feedback)
    db.commit()
    return {"message": "Feedback submitted successfully."}

