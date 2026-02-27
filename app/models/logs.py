from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import TimestampMixin


class VoteLog(Base, TimestampMixin):
    __tablename__ = "vote_logs"

    id: Mapped[int] = mapped_column(primary_key=True)

    voter_id: Mapped[int] = mapped_column(ForeignKey("voters.id"))
    election_id: Mapped[int] = mapped_column(ForeignKey("elections.id"))
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"))

    vote_hash: Mapped[str] = mapped_column(String(255))
    blockchain_tx_hash: Mapped[str] = mapped_column(String(255))
    ip_address: Mapped[str] = mapped_column(String(100))

    voter = relationship("Voter", back_populates="votes")


class FraudAlert(Base, TimestampMixin):
    __tablename__ = "fraud_alerts"

    id: Mapped[int] = mapped_column(primary_key=True)

    voter_id: Mapped[int] = mapped_column(ForeignKey("voters.id"))

    anomaly_score: Mapped[float] = mapped_column(Float)

    reason: Mapped[str] = mapped_column(String(500))
