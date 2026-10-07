import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, Money, created_at_column, enum_column, new_uuid

import enum

class RecurringFrequency(str, enum.Enum):
    WEEKLY = "WEEKLY"
    BIWEEKLY = "BIWEEKLY"
    MONTHLY = "MONTHLY"


class RecurringStatus(str, enum.Enum):
    DETECTED = "DETECTED"
    CONFIRMED = "CONFIRMED"
    DISMISSED = "DISMISSED"

class RecurringExpense(Base):
    __tablename__ = "recurring_expenses"
    __table_args__ = (UniqueConstraint("user_id", "merchant", name="uq_recurring_user_merchant"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    account_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("accounts.id", ondelete="CASCADE"))
    category_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("categories.id", ondelete="SET NULL"))
    merchant: Mapped[str] = mapped_column(String(150))
    avg_amount: Mapped[Decimal] = mapped_column(Money)
    frequency: Mapped[RecurringFrequency] = mapped_column(enum_column(RecurringFrequency))
    next_due_date: Mapped[date] = mapped_column(Date)
    status: Mapped[RecurringStatus] = mapped_column(enum_column(RecurringStatus), default=RecurringStatus.DETECTED)
    created_at: Mapped[datetime] = created_at_column()
