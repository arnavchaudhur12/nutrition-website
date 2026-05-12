from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.hero import HeroSettingsRead
from app.services.hero_service import HeroService

router = APIRouter()


@router.get("", response_model=HeroSettingsRead)
def get_hero_settings(db: Session = Depends(get_db)) -> HeroSettingsRead:
    return HeroService(db).get_settings()
