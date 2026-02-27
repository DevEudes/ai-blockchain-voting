from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import TimestampMixin


class Candidate(Base, TimestampMixin):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(255))
    manifesto: Mapped[str] = mapped_column(String(1000))

    election_id: Mapped[int] = mapped_column(ForeignKey("elections.id"))

    election = relationship("Election", back_populates="candidates")
