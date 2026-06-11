from datetime import datetime

from sqlalchemy import DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class VisitorCounter(Base):
    __tablename__ = "visitor_counter"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    total_visitors: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
