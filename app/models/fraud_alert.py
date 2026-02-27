from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.models.base import TimestampMixin


class FraudAlert(Base, TimestampMixin):
    __tablename__ = "fraud_alerts"

    id: Mapped[int] = mapped_column(primary_key=True)

    voter_id: Mapped[int] = mapped_column(ForeignKey("voters.id"))

    anomaly_score: Mapped[float] = mapped_column(Float)

    reason: Mapped[str] = mapped_column(String(500))
