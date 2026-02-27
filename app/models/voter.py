from sqlalchemy import Column, String, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import TimestampMixin
from app.core.roles import ROLE_VOTER


class Voter(Base, TimestampMixin):
    __tablename__ = "voters"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    biometric_embedding: Mapped[str] = mapped_column(Text, nullable=False)

    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_voted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    wallet_address: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    role = Column(String(20), default=ROLE_VOTER)

    votes = relationship("VoteLog", back_populates="voter")
