import uuid
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.alert import Alert
from app.models.alert import AlertType 
from app.models.recurring import RecurringStatus
from app.models.recurring import RecurringExpense

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


def create_due_alerts(db: Session, user_id: uuid.UUID, today: date | None = None) -> None:
    today = today or date.today()
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

