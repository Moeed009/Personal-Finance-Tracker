import uuid
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.core.money import ZERO, money
from app.models.recurring import RecurringFrequency, RecurringStatus , RecurringExpense
from app.models.transaction import TransactionType , Transaction
from app.services.queries import analysis_scope

INTERVAL_DAYS = {RecurringFrequency.WEEKLY: 7, RecurringFrequency.BIWEEKLY: 14, RecurringFrequency.MONTHLY: 30}
MONTHLY_FACTOR = {
    RecurringFrequency.WEEKLY: Decimal(52) / 12,
    RecurringFrequency.BIWEEKLY: Decimal(26) / 12,
    RecurringFrequency.MONTHLY: Decimal(1),
}
MIN_OCCURRENCES = 3
GAP_TOLERANCE_DAYS = 3
AMOUNT_TOLERANCE = Decimal("0.10")


def evaluate_series(dates: list[date], amounts: list[Decimal]) -> tuple[RecurringFrequency, Decimal] | None:
    if len(dates) < MIN_OCCURRENCES:
        return None
    ordered = sorted(zip(dates, amounts))
    gaps = [(b[0] - a[0]).days for a, b in zip(ordered, ordered[1:])]
    frequency = next(
        (
            freq
            for freq, days in INTERVAL_DAYS.items()
            if all(abs(gap - days) <= GAP_TOLERANCE_DAYS for gap in gaps)
        ),
        None,
    )
    if frequency is None:
        return None
    average = sum(amounts, Decimal("0")) / len(amounts)
    if any(abs(amount - average) > average * AMOUNT_TOLERANCE for amount in amounts):
        return None
    return frequency, money(average)


def detect(db: Session, user_id: uuid.UUID) -> list[RecurringExpense]:
    transactions = db.scalars(
        select(Transaction)
        .where(analysis_scope(user_id), Transaction.type == TransactionType.EXPENSE, Transaction.merchant.is_not(None))
        .order_by(Transaction.transaction_date)
    ).all()
    groups: dict[str, list[Transaction]] = defaultdict(list)
    for txn in transactions:
        groups[txn.merchant].append(txn)
    existing = {r.merchant: r for r in db.scalars(select(RecurringExpense).where(RecurringExpense.user_id == user_id))}
    found: list[RecurringExpense] = []
    for merchant, items in groups.items():
        outcome = evaluate_series([t.transaction_date for t in items], [t.amount for t in items])
        if outcome is None:
            continue
        frequency, average = outcome
        latest = items[-1]
        record = existing.get(merchant)
        if record is not None and record.status == RecurringStatus.DISMISSED:
            continue
        if record is None:
            record = RecurringExpense(user_id=user_id, merchant=merchant, status=RecurringStatus.DETECTED)
            db.add(record)
        record.account_id = latest.account_id
        record.category_id = latest.category_id
        record.avg_amount = average
        record.frequency = frequency
        record.next_due_date = latest.transaction_date + timedelta(days=INTERVAL_DAYS[frequency])
        for txn in items:
            txn.is_recurring = True
        found.append(record)
    db.flush()
    return found


def run_detection(db: Session, user_id: uuid.UUID) -> list[RecurringExpense]:
    found = detect(db, user_id)
    db.commit()
    return found


def monthly_cost(items: list[RecurringExpense]) -> Decimal:
    total = sum(
        (i.avg_amount * MONTHLY_FACTOR[i.frequency] for i in items if i.status != RecurringStatus.DISMISSED),
        ZERO,
    )
    return money(total)


def list_recurring(db: Session, user_id: uuid.UUID, status: RecurringStatus | None = None) -> list[RecurringExpense]:
    query = select(RecurringExpense).where(RecurringExpense.user_id == user_id)
    if status:
        query = query.where(RecurringExpense.status == status)
    return list(db.scalars(query.order_by(RecurringExpense.next_due_date)))


def set_status(db: Session, user_id: uuid.UUID, recurring_id: uuid.UUID, status: str) -> RecurringExpense:
    record = db.scalar(
        select(RecurringExpense).where(RecurringExpense.id == recurring_id, RecurringExpense.user_id == user_id)
    )
    if record is None:
        raise NotFoundError("Recurring expense not found")
    record.status = RecurringStatus(status)
    db.commit()
    return record
