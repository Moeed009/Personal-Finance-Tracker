import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.account import AccountType
from app.schemas.common import MoneyValue, ORMModel


class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: AccountType
    opening_balance: MoneyValue = Decimal("0.00")


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    type: AccountType | None = None
    opening_balance: MoneyValue | None = None


class AccountRead(ORMModel):
    id: uuid.UUID
    name: str
    type: AccountType
    opening_balance: Decimal
    balance: Decimal
    created_at: datetime


class AccountSummary(BaseModel):
    accounts: list[AccountRead]
    total_balance: Decimal


class AccountBalanceSummary(BaseModel):
    account_id: uuid.UUID
    account_name: str
    account_type: AccountType
    opening_balance: Decimal
    current_balance: Decimal
    total_income: Decimal
    total_expense: Decimal
    transfer_in: Decimal
    transfer_out: Decimal
    transaction_count: int
    last_transaction_date: date | None