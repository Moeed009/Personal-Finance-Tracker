import uuid
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class PeriodSummary(BaseModel):
    start_date: date
    end_date: date
    income: Decimal
    expense: Decimal
    savings: Decimal
    savings_rate_percent: Decimal


class CategorySpend(BaseModel):
    category_id: uuid.UUID | None
    category_name: str
    total: Decimal
    percentage: Decimal
    


class TrendPoint(BaseModel):
    month: date
    income: Decimal
    expense: Decimal
    savings: Decimal
    savings_rate_percent: Decimal | None = None


class TopItem(BaseModel):
    name: str
    total: Decimal
    count: int
    percentage: Decimal | None = None


class TopResult(BaseModel):
    merchants: list[TopItem]
    categories: list[TopItem]


class UnusualItem(BaseModel):
    kind: Literal["TRANSACTION", "CATEGORY"]
    category_id: uuid.UUID | None
    category_name: str
    transaction_id: uuid.UUID | None = None
    amount: Decimal
    threshold: Decimal
    expected_amount: Decimal | None = None
    deviation_percent: Decimal | None = None
    detected_at: date | None = None
    message: str


class BudgetInsight(BaseModel):
    budget_id: uuid.UUID
    category_id: uuid.UUID
    category_name: str
    budget_amount: Decimal
    spent_amount: Decimal
    remaining_amount: Decimal
    utilization_percent: Decimal
    status: Literal["NORMAL", "WARNING", "EXCEEDED"]
    period_start: date
    period_end: date
    message: str


class RecurringInsight(BaseModel):
    merchant_name: str
    amount: Decimal
    frequency: str
    next_due_date: date | None = None
    confidence: Decimal
    message: str


class InsightMessage(BaseModel):
    kind: Literal[
        "SPENDING",
        "SAVING",
        "TREND",
        "BUDGET",
        "UNUSUAL",
        "RECURRING",
        "INCOME",
    ]
    title: str
    message: str
    severity: Literal["INFO", "WARNING", "CRITICAL"]
    period_start: date | None = None
    period_end: date | None = None
    category_id: uuid.UUID | None = None
    category_name: str | None = None
    amount: Decimal | None = None
    threshold: Decimal | None = None
    recommendation: str | None = None


class InsightSummary(BaseModel):
    total_insights: int
    info_count: int
    warning_count: int
    critical_count: int