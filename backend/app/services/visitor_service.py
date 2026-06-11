from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.visitor import VisitorCounter


class VisitorService:
    def __init__(self, db: Session):
        self.db = db

    def get_total_visitors(self) -> dict[str, int]:
        counter = self._get_or_create_counter()
        return {"total_visitors": counter.total_visitors}

    def track_visit(self) -> dict[str, int]:
        counter = self._get_or_create_counter()
        counter.total_visitors += 1
        self.db.add(counter)
        self.db.commit()
        self.db.refresh(counter)
        return {"total_visitors": counter.total_visitors}

    def _get_or_create_counter(self) -> VisitorCounter:
        counter = self.db.get(VisitorCounter, 1)
        if counter:
            return counter

        counter = VisitorCounter(id=1, total_visitors=0)
        self.db.add(counter)
        self.db.commit()
        self.db.refresh(counter)
        return counter
