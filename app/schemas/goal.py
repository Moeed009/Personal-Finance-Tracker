import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.goal import GoalStatus
from app.schemas.common import PositiveMoney


class GoalCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    target_amount: PositiveMoney
    target_date: date


class GoalUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    target_amount: PositiveMoney | None = None
    target_date: date | None = None
    status: GoalStatus | None = None


class ContributionCreate(BaseModel):
    amount: PositiveMoney


class GoalRead(BaseModel):
    id: uuid.UUID
    name: str
    target_amount: Decimal
    saved_amount: Decimal
    target_date: date
    status: GoalStatus
    progress_percent: Decimal
    remaining_amount: Decimal
    required_monthly_saving: Decimal
