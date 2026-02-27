from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import TimestampMixin
from datetime import datetime
from typing import List

from app.models.candidate import Candidate


class Election(Base, TimestampMixin):
    __tablename__ = "elections"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(500))

    start_date: Mapped[datetime] = mapped_column(DateTime)
    end_date: Mapped[datetime] = mapped_column(DateTime)

    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    candidates: Mapped[List["Candidate"]] = relationship(
        "Candidate", back_populates="election"
    )
