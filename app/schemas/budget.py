import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.models.budget import BudgetStatus
from app.schemas.common import PositiveMoney


class BudgetCreate(BaseModel):
    category_id: uuid.UUID
    month: date
    limit_amount: PositiveMoney


class BudgetUpdate(BaseModel):
    limit_amount: PositiveMoney


class BudgetRead(BaseModel):
    id: uuid.UUID
    category_id: uuid.UUID
    category_name: str
    month: date
    limit_amount: Decimal
    spent: Decimal
    remaining: Decimal
    percent_used: Decimal
    status: BudgetStatus
