
import uuid
from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

from app.core.dates import add_months, first_of_month, month_bounds
from app.core.money import ZERO, money, percent
from app.models.alert import AlertType
from app.models.category import Category
from app.models.transaction import Transaction, TransactionType
from app.schemas.insight import (
    CategorySpend,
    InsightMessage,
    PeriodSummary,
    TopItem,
    TopResult,
    TrendPoint,
    UnusualItem,
)
from app.services import alert_service
from app.services.queries import analysis_scope

MIN_HISTORY = 5
HISTORY_MONTHS = 6
CATEGORY_SPIKE_RATIO = Decimal("1.5")
MESSAGE_THRESHOLD = Decimal("20")


def period_summary(db: Session, user_id: uuid.UUID, start: date, end: date) -> PeriodSummary:
    rows = db.execute(
        select(Transaction.type, func.sum(Transaction.amount))
        .where(
            analysis_scope(user_id),
            Transaction.transaction_date >= start,
            Transaction.transaction_date <= end,
        )
        .group_by(Transaction.type)
    ).all()
    totals = {transaction_type: money(total) for transaction_type, total in rows}
    income = totals.get(TransactionType.INCOME, ZERO)
    expense = totals.get(TransactionType.EXPENSE, ZERO)
    savings = money(income - expense)
    savings_rate = ZERO
    if income > ZERO:
        savings_rate = money(savings / income * 100)
    return PeriodSummary(
        start_date=start,
        end_date=end,
        income=income,
        expense=expense,
        savings=savings,
        savings_rate_percent=savings_rate,
    )


def spending_by_category(db: Session, user_id: uuid.UUID, start: date, end: date) -> list[CategorySpend]:
    rows = db.execute(
        select(
            Transaction.category_id,
            Category.name,
            func.sum(Transaction.amount).label("total"),
        )
        .outerjoin(Category, Category.id == Transaction.category_id)
        .where(
            analysis_scope(user_id),
            Transaction.type == TransactionType.EXPENSE,
            Transaction.transaction_date >= start,
            Transaction.transaction_date <= end,
        )
        .group_by(Transaction.category_id, Category.name)
        .order_by(func.sum(Transaction.amount).desc())
    ).all()
    grand_total = sum((money(total) for _, _, total in rows), ZERO)
    return [
        CategorySpend(
            category_id=category_id,
            category_name=name or "Uncategorized",
            total=money(total),
            percentage=percent(money(total), grand_total),
        )
        for category_id, name, total in rows
    ]


def trends(
    db: Session,
    user_id: uuid.UUID,
    months: int,
    end_month: date | None = None,
) -> list[TrendPoint]:
    last = first_of_month(end_month or date.today())
    first = add_months(last, -months)
    start = first
    _, end = month_bounds(last)
    year = extract("year", Transaction.transaction_date)
    month = extract("month", Transaction.transaction_date)

    rows = db.execute(
        select(year, month, Transaction.type, func.sum(Transaction.amount))
        .where(
            analysis_scope(user_id),
            Transaction.transaction_date >= start,
            Transaction.transaction_date <= end,
        )
        .group_by(year, month, Transaction.type)
    ).all()

    buckets: dict[date, dict[TransactionType, Decimal]] = defaultdict(dict)

    for year_value, month_value, transaction_type, total in rows:
        buckets[date(int(year_value), int(month_value), 1)][transaction_type] = money(total)

    points: list[TrendPoint] = []

    for offset in range(months + 1):
        current = add_months(first, offset)
        income = buckets[current].get(TransactionType.INCOME, ZERO)
        expense = buckets[current].get(TransactionType.EXPENSE, ZERO)
        savings = money(income - expense)

        savings_rate = ZERO
        if income > ZERO:
            savings_rate = money(savings / income * 100)

        if offset > 0:
            points.append(
                TrendPoint(
                    month=current,
                    income=income,
                    expense=expense,
                    savings=savings,
                    savings_rate_percent=savings_rate,
                )
            )

    return points


def top_items(
    db: Session,
    user_id: uuid.UUID,
    start: date,
    end: date,
    limit: int,
) -> TopResult:
    base = [
        analysis_scope(user_id),
        Transaction.type == TransactionType.EXPENSE,
        Transaction.transaction_date >= start,
        Transaction.transaction_date <= end,
    ]
    total_sum = func.sum(Transaction.amount)
    total_expense = db.scalar(select(func.sum(Transaction.amount)).where(*base))
    total_expense = money(total_expense or ZERO)

    merchants = db.execute(
        select(Transaction.merchant, total_sum, func.count())
        .where(*base, Transaction.merchant.is_not(None))
        .group_by(Transaction.merchant)
        .order_by(total_sum.desc())
        .limit(limit)
    ).all()

    categories = db.execute(
        select(Category.name, total_sum, func.count())
        .join(Category, Category.id == Transaction.category_id)
        .where(*base)
        .group_by(Category.name)
        .order_by(total_sum.desc())
        .limit(limit)
    ).all()

    return TopResult(
        merchants=[
            TopItem(
                name=name,
                total=money(total),
                count=count,
                percentage=percent(money(total), total_expense),
            )
            for name, total, count in merchants
        ],
        categories=[
            TopItem(
                name=name,
                total=money(total),
                count=count,
                percentage=percent(money(total), total_expense),
            )
            for name, total, count in categories
        ],
    )


def plain_language_messages(
    db: Session,
    user_id: uuid.UUID,
    month: date | None = None,
) -> list[InsightMessage]:
    current = first_of_month(month or date.today())
    previous = add_months(current, -1)
    current_start, current_end = month_bounds(current)
    previous_start, previous_end = month_bounds(previous)

    current_spending = spending_by_category(
        db,
        user_id,
        current_start,
        current_end,
    )
    previous_spending = spending_by_category(
        db,
        user_id,
        previous_start,
        previous_end,
    )

    now_spend = {
        category.category_name: category.total
        for category in current_spending
    }
    before_spend = {
        category.category_name: category.total
        for category in previous_spending
    }

    current_month_label = current.strftime("%B %Y")
    previous_month_label = previous.strftime("%B %Y")

    messages: list[InsightMessage] = []

    for name, before in before_spend.items():
        if before <= ZERO:
            continue

        current_total = now_spend.get(name, ZERO)
        change = money((current_total - before) / before * 100)

        if abs(change) < MESSAGE_THRESHOLD:
            continue

        if change > ZERO:
            direction = "higher"
            severity = "WARNING"
            title = f"{name} spending increased"
        else:
            direction = "lower"
            severity = "INFO"
            title = f"{name} spending decreased"

        message = (
            f"{name} spending for {current_month_label} is "
            f"{abs(change):.0f} percent {direction} than {previous_month_label}"
        )

        messages.append(
            InsightMessage(
                kind="SPENDING",
                title=title,
                message=message,
                severity=severity,
                period_start=current_start,
                period_end=current_end,
                category_name=name,
                amount=current_total,
                recommendation=(
                    "Review recent transactions in this category."
                    if change > ZERO
                    else None
                ),
            )
        )

    summary = period_summary(
        db,
        user_id,
        current_start,
        current_end,
    )

    if summary.income > ZERO:
        rate = summary.savings_rate_percent
        severity = "INFO"

        if rate < ZERO:
            severity = "CRITICAL"
        elif rate < Decimal("10"):
            severity = "WARNING"

        messages.append(
            InsightMessage(
                kind="SAVING",
                title=f"{current_month_label} savings",
                message=(
                    f"You saved {rate:.0f} percent of your income "
                    f"in {current_month_label}"
                ),
                severity=severity,
                period_start=current_start,
                period_end=current_end,
                amount=summary.savings,
                recommendation=(
                    "Review your largest expense categories."
                    if rate < Decimal("10")
                    else None
                ),
            )
        )

    return messages


def _mean_and_deviation(
    values: list[Decimal],
) -> tuple[Decimal, Decimal]:
    mean = sum(values, Decimal("0")) / len(values)
    variance = sum(
        ((value - mean) ** 2 for value in values),
        Decimal("0"),
    ) / len(values)
    return mean, variance.sqrt()


def _history_start(day: date) -> date:
    return add_months(first_of_month(day), -HISTORY_MONTHS)


def _transaction_threshold(
    history: list[Decimal],
) -> Decimal | None:
    if len(history) < MIN_HISTORY:
        return None

    mean, deviation = _mean_and_deviation(history)
    return money(mean + Decimal("2") * deviation)


def _category_name(
    db: Session,
    category_id: uuid.UUID,
) -> str:
    category = db.get(Category, category_id)
    return category.name if category else "Uncategorized"


def check_transaction(
    db: Session,
    txn: Transaction,
) -> UnusualItem | None:
    if (
        txn.type != TransactionType.EXPENSE
        or txn.category_id is None
        or txn.transfer_group_id is not None
    ):
        return None

    history = list(
        db.scalars(
            select(Transaction.amount).where(
                analysis_scope(txn.user_id),
                Transaction.type == TransactionType.EXPENSE,
                Transaction.category_id == txn.category_id,
                Transaction.transaction_date >= _history_start(
                    txn.transaction_date
                ),
                Transaction.transaction_date < txn.transaction_date,
            )
        )
    )

    threshold = _transaction_threshold(history)

    if threshold is None or txn.amount <= threshold:
        return None

    name = _category_name(db, txn.category_id)

    expected_amount = None
    deviation_percent = None

    if history:
        expected_amount = money(
            sum(history, ZERO) / len(history)
        )

        if expected_amount > ZERO:
            deviation_percent = money(
                (txn.amount - expected_amount)
                / expected_amount
                * 100
            )

    transaction_date_label = txn.transaction_date.strftime(
        "%B %-d, %Y"
    ) if __import__("os").name != "nt" else txn.transaction_date.strftime(
        "%B %#d, %Y"
    )

    message = (
        f"Unusual {name} expense of {txn.amount} "
        f"on {transaction_date_label} "
        f"(usual upper limit {threshold})"
    )

    alert_service.create_alert(
        db,
        txn.user_id,
        AlertType.UNUSUAL_SPENDING,
        message,
        f"unusual:txn:{txn.id}",
    )

    return UnusualItem(
        kind="TRANSACTION",
        category_id=txn.category_id,
        category_name=name,
        transaction_id=txn.id,
        amount=txn.amount,
        threshold=threshold,
        expected_amount=expected_amount,
        deviation_percent=deviation_percent,
        detected_at=txn.transaction_date,
        message=message,
    )


def detect_unusual(
    db: Session,
    user_id: uuid.UUID,
    month: date | None = None,
    commit: bool = True,
) -> list[UnusualItem]:
    target_month = first_of_month(month or date.today())
    start, end = month_bounds(target_month)
    history_from = add_months(target_month, -HISTORY_MONTHS)
    month_label = target_month.strftime("%B %Y")

    expenses = db.scalars(
        select(Transaction).where(
            analysis_scope(user_id),
            Transaction.type == TransactionType.EXPENSE,
            Transaction.category_id.is_not(None),
            Transaction.transaction_date >= history_from,
            Transaction.transaction_date <= end,
        ).order_by(Transaction.transaction_date)
    ).all()

    by_category: dict[uuid.UUID, list[Transaction]] = defaultdict(list)

    for txn in expenses:
        by_category[txn.category_id].append(txn)

    findings: list[UnusualItem] = []

    for category_id, items in by_category.items():
        name = _category_name(db, category_id)

        for txn in (
            item
            for item in items
            if start <= item.transaction_date <= end
        ):
            window_start = _history_start(txn.transaction_date)

            history = [
                item.amount
                for item in items
                if window_start <= item.transaction_date < txn.transaction_date
                and item.id != txn.id
            ]

            threshold = _transaction_threshold(history)

            if threshold is not None and txn.amount > threshold:
                expected_amount = money(
                    sum(history, ZERO) / len(history)
                )

                deviation_percent = None

                if expected_amount > ZERO:
                    deviation_percent = money(
                        (txn.amount - expected_amount)
                        / expected_amount
                        * 100
                    )

                transaction_date_label = (
                    txn.transaction_date.strftime("%B %#d, %Y")
                    if __import__("os").name == "nt"
                    else txn.transaction_date.strftime("%B %-d, %Y")
                )

                message = (
                    f"Unusual {name} expense of {txn.amount} "
                    f"on {transaction_date_label} "
                    f"(usual upper limit {threshold})"
                )

                findings.append(
                    UnusualItem(
                        kind="TRANSACTION",
                        category_id=category_id,
                        category_name=name,
                        transaction_id=txn.id,
                        amount=txn.amount,
                        threshold=threshold,
                        expected_amount=expected_amount,
                        deviation_percent=deviation_percent,
                        detected_at=txn.transaction_date,
                        message=message,
                    )
                )

                alert_service.create_alert(
                    db,
                    user_id,
                    AlertType.UNUSUAL_SPENDING,
                    message,
                    f"unusual:txn:{txn.id}",
                )

        month_total = sum(
            (
                txn.amount
                for txn in items
                if start <= txn.transaction_date <= end
            ),
            ZERO,
        )

        previous_totals: list[Decimal] = []

        for back in (1, 2, 3):
            previous_start, previous_end = month_bounds(
                add_months(target_month, -back)
            )

            previous_total = sum(
                (
                    txn.amount
                    for txn in items
                    if previous_start
                    <= txn.transaction_date
                    <= previous_end
                ),
                ZERO,
            )

            previous_totals.append(previous_total)

        average = sum(
            previous_totals,
            ZERO,
        ) / len(previous_totals)

        if (
            average > ZERO
            and month_total > average * CATEGORY_SPIKE_RATIO
        ):
            rise = money(
                (month_total - average)
                / average
                * 100
            )

            threshold = money(
                average * CATEGORY_SPIKE_RATIO
            )

            message = (
                f"{name} spending for {month_label} "
                f"({money(month_total)}) is "
                f"{rise:.0f} percent above your 3-month average"
            )

            findings.append(
                UnusualItem(
                    kind="CATEGORY",
                    category_id=category_id,
                    category_name=name,
                    amount=money(month_total),
                    threshold=threshold,
                    expected_amount=money(average),
                    deviation_percent=rise,
                    detected_at=target_month,
                    message=message,
                )
            )

            alert_service.create_alert(
                db,
                user_id,
                AlertType.UNUSUAL_SPENDING,
                message,
                f"unusual:cat:{category_id}:{target_month.strftime('%Y-%m')}",
            )

    if commit:
        db.commit()

    return findings
