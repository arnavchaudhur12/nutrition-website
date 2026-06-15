from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_admin
from app.db.session import get_db
from app.services.metrics_service import MetricsService

router = APIRouter()


@router.get("")
def get_metrics(
    period: str = "all_time",
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
) -> dict[str, object]:
    return MetricsService(db).get_dashboard_snapshot(period)
