from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.schemas.budget import BudgetRead
from app.schemas.insight import CategorySpend
from app.schemas.recurring import RecurringRead


class MonthlyReport(BaseModel):
    month: date
    income: Decimal
    expense: Decimal
    savings: Decimal
    categories: list[CategorySpend]
    budgets: list[BudgetRead]
    recurring: list[RecurringRead]
    recurring_monthly_cost: Decimal
