import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, String, UniqueConstraint, Uuid, false, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, JSONType, Money, created_at_column, enum_column, new_uuid

import enum

class TransactionType(str, enum.Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"
    TRANSFER = "TRANSFER"

class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("account_id", "dedupe_hash", name="uq_transactions_account_dedupe"),
        Index("ix_transactions_user_date", "user_id", "transaction_date"),
        Index("ix_transactions_user_category", "user_id", "category_id"),
        Index("ix_transactions_account", "account_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"))
    account_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("accounts.id", ondelete="CASCADE"))
    category_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("categories.id", ondelete="SET NULL"))
    import_batch_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("import_batches.id", ondelete="SET NULL"), index=True
    )
    type: Mapped[TransactionType] = mapped_column(enum_column(TransactionType))
    amount: Mapped[Decimal] = mapped_column(Money)
    description: Mapped[str] = mapped_column(String(300))
    merchant: Mapped[str | None] = mapped_column(String(150), index=True)
    transaction_date: Mapped[date] = mapped_column(Date)
    transfer_group_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, index=True)
    dedupe_hash: Mapped[str | None] = mapped_column(String(64))
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_data: Mapped[dict] = mapped_column(JSONType, default=dict)
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())