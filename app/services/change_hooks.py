import logging
import uuid
from collections.abc import Iterable
from datetime import date

from sqlalchemy.orm import Session

from app.core.dates import first_of_month
from app.models.transaction import Transaction
from app.services import budget_service, insight_service

logger = logging.getLogger(__name__)


def transactions_changed(
    db: Session,
    user_id: uuid.UUID,
    days: Iterable[date],
    new_or_changed: Iterable[Transaction] = (),
) -> None:
    try:
        budget_service.refresh_statuses(db, user_id, set(days))

        for txn in new_or_changed:
            insight_service.check_transaction(db, txn)

        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Could not refresh alerts after a transaction change")


def statement_imported(db: Session, user_id: uuid.UUID, days: Iterable[date]) -> None:
    months = {first_of_month(day) for day in days}

    if not months:
        return

    try:
        budget_service.refresh_statuses(db, user_id, months)

        for month in months:
            insight_service.detect_unusual(db, user_id, month, commit=False)

        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Could not refresh alerts after an import")
