import calendar
import uuid
from datetime import date, timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.alert import Alert
from app.models.alert import AlertType 
from app.models.recurring import RecurringFrequency, RecurringStatus
from app.models.recurring import RecurringExpense
from app.services.recurring_service import INTERVAL_DAYS

DUE_SOON_DAYS = 3


def create_alert(
    db: Session, user_id: uuid.UUID, alert_type: AlertType, message: str, reference_key: str | None = None
) -> Alert | None:
    if reference_key and db.scalar(
        select(Alert.id).where(Alert.user_id == user_id, Alert.reference_key == reference_key)
    ):
        return None
    alert = Alert(user_id=user_id, alert_type=alert_type, message=message, reference_key=reference_key)
    db.add(alert)
    db.flush()
    return alert


def _roll_due_dates(db: Session, user_id: uuid.UUID, today: date) -> None:
    stale = db.scalars(
        select(RecurringExpense).where(
            RecurringExpense.user_id == user_id,
            RecurringExpense.status != RecurringStatus.DISMISSED,
            RecurringExpense.next_due_date < today,
        )
    )
    for item in stale:
        due = item.next_due_date
        while due < today:
            due = _next_occurrence(due, item.frequency)
        item.next_due_date = due
    db.flush()


def _next_occurrence(due: date, frequency: RecurringFrequency) -> date:
    if frequency != RecurringFrequency.MONTHLY:
        return due + timedelta(days=INTERVAL_DAYS[frequency])
    year, month = (due.year + 1, 1) if due.month == 12 else (due.year, due.month + 1)
    return date(year, month, min(due.day, calendar.monthrange(year, month)[1]))


def create_due_alerts(db: Session, user_id: uuid.UUID, today: date | None = None) -> None:
    today = today or date.today()
    _roll_due_dates(db, user_id, today)
    horizon = today + timedelta(days=DUE_SOON_DAYS)
    items = db.scalars(
        select(RecurringExpense).where(
            RecurringExpense.user_id == user_id,
            RecurringExpense.status != RecurringStatus.DISMISSED,
            RecurringExpense.next_due_date >= today,
            RecurringExpense.next_due_date <= horizon,
        )
    )
    for item in items:
        create_alert(
            db,
            user_id,
            AlertType.RECURRING_DUE,
            f"{item.merchant.title()} payment of {item.avg_amount} is due on {item.next_due_date.isoformat()}",
            f"recurring:{item.id}:{item.next_due_date.isoformat()}",
        )
    db.commit()


def list_alerts(db: Session, user_id: uuid.UUID, unread_only: bool = False) -> list[Alert]:
    create_due_alerts(db, user_id)
    query = select(Alert).where(Alert.user_id == user_id)
    if unread_only:
        query = query.where(Alert.is_read.is_(False))
    return list(db.scalars(query.order_by(Alert.created_at.desc())))


def mark_read(db: Session, user_id: uuid.UUID, alert_id: uuid.UUID) -> Alert:
    alert = db.scalar(select(Alert).where(Alert.id == alert_id, Alert.user_id == user_id))
    if alert is None:
        raise NotFoundError("Alert not found")
    alert.is_read = True
    db.commit()
    return alert


def mark_all_read(db: Session, user_id: uuid.UUID) -> int:
    result = db.execute(
        update(Alert)
        .where(Alert.user_id == user_id, Alert.is_read.is_(False))
        .values(is_read=True)
        .execution_options(synchronize_session=False)
    )
    db.commit()
    return result.rowcount or 0
