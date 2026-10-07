import csv
import io
import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dates import first_of_month, month_bounds
from app.models.category import Category
from app.models.transaction import Transaction
from app.schemas.recurring import RecurringRead
from app.schemas.report import MonthlyReport
from app.services import budget_service, insight_service, recurring_service


def monthly_report(db: Session, user_id: uuid.UUID, month: date) -> MonthlyReport:
    month = first_of_month(month)
    start, end = month_bounds(month)
    summary = insight_service.period_summary(db, user_id, start, end)
    recurring = recurring_service.list_recurring(db, user_id)
    return MonthlyReport(
        month=month, income=summary.income, expense=summary.expense, savings=summary.savings,
        categories=insight_service.spending_by_category(db, user_id, start, end),
        budgets=budget_service.list_budgets(db, user_id, month),
        recurring=[RecurringRead.model_validate(r) for r in recurring if r.status.value != "DISMISSED"],
        recurring_monthly_cost=recurring_service.monthly_cost(recurring),
    )

