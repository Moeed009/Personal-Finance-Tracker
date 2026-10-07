import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser
from app.models.recurring import RecurringStatus
from app.schemas.recurring import DetectionResult, RecurringList, RecurringRead, RecurringUpdate
from app.services import recurring_service

router = APIRouter(prefix="/recurring", tags=["Recurring"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=RecurringList)
def list_recurring(user: CurrentUser, db: DbSession, status: RecurringStatus | None = None):
    items = recurring_service.list_recurring(db, user.id, status)
    return RecurringList(
        items=[RecurringRead.model_validate(i) for i in items],
        total_monthly_cost=recurring_service.monthly_cost(items),
    )


@router.post("/detect", response_model=DetectionResult)
def detect_recurring(user: CurrentUser, db: DbSession):
    found = recurring_service.run_detection(db, user.id)
    return DetectionResult(detected=len(found), items=[RecurringRead.model_validate(i) for i in found])


@router.patch("/{recurring_id}", response_model=RecurringRead)
def update_recurring(recurring_id: uuid.UUID, data: RecurringUpdate, user: CurrentUser, db: DbSession):
    return recurring_service.set_status(db, user.id, recurring_id, data.status)
