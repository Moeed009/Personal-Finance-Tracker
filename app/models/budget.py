import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, Money, created_at_column, enum_column, new_uuid

import enum

class BudgetStatus(str, enum.Enum):
    ON_TRACK = "ON_TRACK"
    WARNING = "WARNING"
    EXCEEDED = "EXCEEDED"

class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (UniqueConstraint("user_id", "category_id", "month", name="uq_budgets_user_category_month"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    category_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("categories.id", ondelete="CASCADE"))
    month: Mapped[date] = mapped_column(Date)
    limit_amount: Mapped[Decimal] = mapped_column(Money)
    last_status: Mapped[BudgetStatus] = mapped_column(enum_column(BudgetStatus), default=BudgetStatus.ON_TRACK)
    created_at: Mapped[datetime] = created_at_column()
