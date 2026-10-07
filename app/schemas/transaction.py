import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.transaction import TransactionType
from app.schemas.common import ORMModel, PositiveMoney


class TransactionCreate(BaseModel):
    account_id: uuid.UUID
    type: TransactionType
    amount: PositiveMoney
    transaction_date: date
    description: str = Field(min_length=1, max_length=300)
    category_id: uuid.UUID | None = None
    merchant: str | None = Field(default=None, max_length=150)


class TransactionUpdate(BaseModel):
    account_id: uuid.UUID | None = None
    type: TransactionType | None = None
    amount: PositiveMoney | None = None
    transaction_date: date | None = None
    description: str | None = Field(default=None, min_length=1, max_length=300)
    category_id: uuid.UUID | None = None
    merchant: str | None = Field(default=None, max_length=150)


class TransactionRead(ORMModel):
    id: uuid.UUID
    account_id: uuid.UUID
    category_id: uuid.UUID | None
    import_batch_id: uuid.UUID | None
    type: TransactionType
    amount: Decimal
    description: str
    merchant: str | None
    transaction_date: date
    transfer_group_id: uuid.UUID | None
    is_recurring: bool
    created_at: datetime


class TransactionFilters(BaseModel):
    account_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    type: TransactionType | None = None
    date_from: date | None = None
    date_to: date | None = None
    min_amount: Decimal | None = Field(default=None, ge=0)
    max_amount: Decimal | None = Field(default=None, ge=0)
    search: str | None = Field(default=None, max_length=100)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class TransferCreate(BaseModel):
    from_account_id: uuid.UUID
    to_account_id: uuid.UUID
    amount: PositiveMoney
    transaction_date: date
    description: str = Field(default="Transfer", min_length=1, max_length=300)


class TransferRead(BaseModel):
    transfer_group_id: uuid.UUID
    outgoing: TransactionRead
    incoming: TransactionRead

    
class TransactionSummary(BaseModel):
    opening_balance: Decimal
    total_debit: Decimal
    total_credit: Decimal
    balance: Decimal