import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dates import first_of_month, month_bounds
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.core.money import ZERO, money, percent
from app.models.budget import Budget
from app.models.category import Category
from app.models.budget import  BudgetStatus
from app.models.alert import AlertType
from app.models.category import  CategoryType
from app.models.transaction import TransactionType
from app.models.category import CategoryType
from app.models.transaction import Transaction
from app.schemas.budget import BudgetCreate, BudgetRead, BudgetUpdate
from app.services import alert_service, category_service
from app.services.queries import analysis_scope

WARNING_AT = Decimal("80")
EXCEEDED_AT = Decimal("100")


def status_for(percent_used: Decimal) -> BudgetStatus:
    if percent_used >= EXCEEDED_AT:
        return BudgetStatus.EXCEEDED
    if percent_used >= WARNING_AT:
        return BudgetStatus.WARNING
    return BudgetStatus.ON_TRACK


def _spent_by_category(db: Session, user_id: uuid.UUID, month: date) -> dict[uuid.UUID, Decimal]:
    start, end = month_bounds(month)
    rows = db.execute(
        select(Transaction.category_id, func.sum(Transaction.amount))
        .where(
            analysis_scope(user_id),
            Transaction.type == TransactionType.EXPENSE,
            Transaction.transaction_date >= start,
            Transaction.transaction_date <= end,
            Transaction.category_id.is_not(None),
        )
        .group_by(Transaction.category_id)
    ).all()
    return {category_id: money(total) for category_id, total in rows}


def _build(budget: Budget, category_name: str, spent: Decimal) -> BudgetRead:
    used = percent(spent, budget.limit_amount)
    return BudgetRead(
        id=budget.id,
        category_id=budget.category_id,
        category_name=category_name,
        month=budget.month,
        limit_amount=budget.limit_amount,
        spent=spent,
        remaining=money(budget.limit_amount - spent),
        percent_used=used,
        status=status_for(used),
    )


def list_budgets(db: Session, user_id: uuid.UUID, month: date | None = None) -> list[BudgetRead]:
    month = first_of_month(month or date.today())
    spent = _spent_by_category(db, user_id, month)
    rows = db.execute(
        select(Budget, Category.name)
        .join(Category, Category.id == Budget.category_id)
        .where(Budget.user_id == user_id, Budget.month == month)
        .order_by(Category.name)
    ).all()
    return [_build(budget, name, spent.get(budget.category_id, ZERO)) for budget, name in rows]


def _get(db: Session, user_id: uuid.UUID, budget_id: uuid.UUID) -> Budget:
    budget = db.scalar(select(Budget).where(Budget.id == budget_id, Budget.user_id == user_id))
    if budget is None:
        raise NotFoundError("Budget not found")
    return budget


def _read_one(db: Session, user_id: uuid.UUID, budget: Budget) -> BudgetRead:
    category = db.get(Category, budget.category_id)
    spent = _spent_by_category(db, user_id, budget.month).get(budget.category_id, ZERO)
    return _build(budget, category.name, spent)


def create_budget(db: Session, user_id: uuid.UUID, data: BudgetCreate) -> BudgetRead:
    category = category_service.get_category(db, user_id, data.category_id)
    if category.type == CategoryType.INCOME:
        raise BadRequestError("Budgets can only be set for expense categories")
    month = first_of_month(data.month)
    budget = Budget(user_id=user_id, category_id=category.id, month=month, limit_amount=data.limit_amount)
    db.add(budget)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise ConflictError("A budget for this category and month already exists")
    refresh_statuses(db, user_id, {month})
    db.commit()
    return _read_one(db, user_id, budget)


def update_budget(db: Session, user_id: uuid.UUID, budget_id: uuid.UUID, data: BudgetUpdate) -> BudgetRead:
    budget = _get(db, user_id, budget_id)
    budget.limit_amount = data.limit_amount
    db.flush()
    refresh_statuses(db, user_id, {budget.month})
    db.commit()
    return _read_one(db, user_id, budget)


def delete_budget(db: Session, user_id: uuid.UUID, budget_id: uuid.UUID) -> None:
    db.delete(_get(db, user_id, budget_id))
    db.commit()


def refresh_statuses(db: Session, user_id: uuid.UUID, months: set[date]) -> None:
    for month in {first_of_month(m) for m in months}:
        budgets = db.execute(
            select(Budget, Category.name)
            .join(Category, Category.id == Budget.category_id)
            .where(Budget.user_id == user_id, Budget.month == month)
        ).all()
        if not budgets:
            continue
        spent = _spent_by_category(db, user_id, month)
        for budget, name in budgets:
            used = percent(spent.get(budget.category_id, ZERO), budget.limit_amount)
            new_status = status_for(used)
            if new_status == budget.last_status:
                continue
            budget.last_status = new_status
            label = f"{name} budget for {month.strftime('%B %Y')}"
            if new_status == BudgetStatus.WARNING:
                alert_service.create_alert(
                    db, user_id, AlertType.BUDGET_WARNING, f"{label} has reached {used}% of its limit"
                )
            elif new_status == BudgetStatus.EXCEEDED:
                alert_service.create_alert(
                    db, user_id, AlertType.BUDGET_EXCEEDED, f"{label} is exceeded ({used}% used)"
                )
