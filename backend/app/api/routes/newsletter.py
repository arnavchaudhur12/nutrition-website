from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.newsletter import NewsletterSubscriber
from app.schemas.newsletter import NewsletterSubscribeRequest

router = APIRouter()


@router.post("/subscribe")
def subscribe(payload: NewsletterSubscribeRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    subscriber = NewsletterSubscriber(email=payload.email)
    db.add(subscriber)
    db.commit()
    return {"message": "Subscribed successfully."}

