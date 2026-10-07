import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, Money, created_at_column, enum_column, new_uuid

import enum

class GoalStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"

class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    target_amount: Mapped[Decimal] = mapped_column(Money)
    saved_amount: Mapped[Decimal] = mapped_column(Money, default=Decimal("0.00"))
    target_date: Mapped[date] = mapped_column(Date)
    status: Mapped[GoalStatus] = mapped_column(enum_column(GoalStatus), default=GoalStatus.ACTIVE)
    created_at: Mapped[datetime] = created_at_column()
