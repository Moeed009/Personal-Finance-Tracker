import uuid
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

from app.models.recurring import RecurringFrequency, RecurringStatus
from app.schemas.common import ORMModel


class RecurringRead(ORMModel):
    id: uuid.UUID
    account_id: uuid.UUID
    category_id: uuid.UUID | None
    merchant: str
    avg_amount: Decimal
    frequency: RecurringFrequency
    next_due_date: date
    status: RecurringStatus


class RecurringList(BaseModel):
    items: list[RecurringRead]
    total_monthly_cost: Decimal


class RecurringUpdate(BaseModel):
    status: Literal["CONFIRMED", "DISMISSED"]


class DetectionResult(BaseModel):
    detected: int
    items: list[RecurringRead]
